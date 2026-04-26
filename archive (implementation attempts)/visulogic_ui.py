import json
import os
import random
import base64
import requests
import re
from pathlib import Path

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cache for loaded data
_eval_data = None
_train_data = None

def load_visulogic_data(mode='eval'):
    """Load VisuLogic dataset from HuggingFace API"""
    global _eval_data, _train_data
    
    if mode == 'eval' and _eval_data is not None:
        return _eval_data
    elif mode == 'train' and _train_data is not None:
        return _train_data
    
    try:
        if mode == 'eval':
            # Use the HuggingFace datasets API to get eval data
            url = "https://datasets-server.huggingface.co/rows?dataset=VisuLogic%2FVisuLogic&config=default&split=train&offset=0&length=100"
        elif mode == 'train':
            # Use the HuggingFace datasets API to get train data
            url = "https://datasets-server.huggingface.co/first-rows?dataset=VisuLogic%2FVisuLogic-Train&config=default&split=train"
        
        print(f"Fetching VisuLogic {mode} data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        puzzles = []
        
        if mode == 'eval' and 'rows' in data:
            # Extract the actual puzzle data from the eval response
            for row in data['rows']:
                if 'row' in row:
                    puzzle_data = row['row']
                    puzzles.append(puzzle_data)
        elif mode == 'train' and 'rows' in data:
            # Extract the actual puzzle data from the train response
            for row in data['rows']:
                if 'row' in row:
                    puzzle_data = row['row']
                    puzzles.append(puzzle_data)
        else:
            print(f"Unexpected response format: {data}")
            raise ValueError("Unexpected response format from HuggingFace API")
        
        if mode == 'eval':
            _eval_data = puzzles
        elif mode == 'train':
            _train_data = puzzles
            
        print(f"Loaded {len(puzzles)} puzzles from VisuLogic {mode} dataset")
        return puzzles
            
    except Exception as e:
        print(f"Error loading VisuLogic {mode} data: {e}")
        raise

def get_image_base64(image_path_or_url, mode='eval'):
    """Convert image to base64 string from HuggingFace URL"""
    try:
        # If it's already a full URL (from eval dataset), use it directly
        if image_path_or_url.startswith('http'):
            image_url = image_path_or_url
        else:
            # Construct HuggingFace URL for train images  
            image_url = f"https://huggingface.co/datasets/VisuLogic/VisuLogic-Train/resolve/main/{image_path_or_url}"
        
        print(f"Fetching image from: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Error fetching image {image_path_or_url}: {e}")
        return None

def get_random_puzzle(mode='eval'):
    """Get a random puzzle from the dataset"""
    try:
        data = load_visulogic_data(mode)
        if not data:
            print(f"No data loaded for mode {mode}")
            return None
        
        print(f"Data loaded successfully, {len(data)} puzzles available")
        puzzle = random.choice(data)
        
        formatted = format_puzzle(puzzle, mode)
        return formatted
    except Exception as e:
        print(f"Error getting random puzzle: {e}")
        return None

def get_puzzle_by_id(puzzle_id, mode='eval'):
    """Get a specific puzzle by ID"""
    try:
        data = load_visulogic_data(mode)
        if not data:
            return None
        
        for puzzle in data:
            if puzzle.get('id') == puzzle_id or puzzle.get('puzzle_id') == puzzle_id:
                return format_puzzle(puzzle, mode)
        
        return None
    except Exception as e:
        print(f"Error getting puzzle by ID: {e}")
        return None

def get_all_puzzles_metadata(mode='eval'):
    """Get metadata for all puzzles"""
    try:
        data = load_visulogic_data(mode)
        if not data:
            return []
        
        metadata = []
        for puzzle in data:
            metadata.append({
                'id': puzzle.get('id', puzzle.get('puzzle_id', '')),
                'puzzle_id': puzzle.get('id', puzzle.get('puzzle_id', '')),
                'category': puzzle.get('category', ''),
                'subcategory': puzzle.get('subcategory', ''),
                'question': puzzle.get('question', '')[:100] + '...' if len(puzzle.get('question', '')) > 100 else puzzle.get('question', '')
            })
        
        return metadata
    except Exception as e:
        print(f"Error getting puzzles metadata: {e}")
        return []

def format_puzzle(puzzle, mode='eval'):
    """Format puzzle data for frontend consumption"""
    if not puzzle:
        print("ERROR: Puzzle is None or empty")
        return None
    
    try:
        # Handle different image formats
        images = []
        
        # Handle eval dataset format (image object with src field)
        if 'image' in puzzle and isinstance(puzzle['image'], dict) and 'src' in puzzle['image']:
            img_url = puzzle['image']['src']
            img_b64 = get_image_base64(img_url, mode)
            if img_b64:
                images.append(f"data:image/png;base64,{img_b64}")
        
        # Handle train dataset format (image path in message field)
        elif 'message' in puzzle and isinstance(puzzle['message'], str):
            # Extract image path from the message JSON
            try:
                message_data = json.loads(puzzle['message'])
                for content in message_data:
                    if isinstance(content, dict) and content.get('type') == 'image':
                        img_path = content.get('image', '')
                        if img_path:
                            img_b64 = get_image_base64(img_path, mode)
                            if img_b64:
                                images.append(f"data:image/png;base64,{img_b64}")
            except:
                pass
        
        # Handle simple image path (some train puzzles have this)
        elif 'image' in puzzle and isinstance(puzzle['image'], str):
            img_b64 = get_image_base64(puzzle['image'], mode)
            if img_b64:
                images.append(f"data:image/png;base64,{img_b64}")
        
        # Extract question and options
        question = puzzle.get('question', '')
        options = []
        clean_question = question
        
        # For train dataset, parse from message field
        if 'message' in puzzle and isinstance(puzzle['message'], str):
            try:
                message_data = json.loads(puzzle['message'])
                for content in message_data:
                    if isinstance(content, dict) and content.get('type') == 'text':
                        text_content = content.get('content', '')
                        # Extract the main question (before the options)
                        lines = text_content.split('\n')
                        for line in lines:
                            if '<image>' in line or 'Divide the following' in line or 'Which' in line or 'What' in line or 'This question includes' in line:
                                clean_question = line.replace('<image>', '').strip()
                                break
                        
                        # Extract options from the text content
                        option_pattern1 = r'([A-D]):\s*([A-D])'
                        matches1 = re.findall(option_pattern1, text_content)
                        if matches1:
                            options = [match[1].strip() for match in matches1]
                        else:
                            option_pattern2 = r'([A-D]):\s*([①②③④⑤⑥\s,]+)'
                            matches2 = re.findall(option_pattern2, text_content)
                            if matches2:
                                options = [match[1].strip() for match in matches2]
                        break
            except:
                pass
        
        # Fallback option parsing from question field
        if not options and question:
            option_pattern1 = r'([A-D]):\s*([A-D])'
            matches1 = re.findall(option_pattern1, question)
            if matches1:
                options = [match[1].strip() for match in matches1]
            else:
                option_pattern2 = r'([A-D]):\s*([①②③④⑤⑥\s,]+)'
                matches2 = re.findall(option_pattern2, question)
                if matches2:
                    options = [match[1].strip() for match in matches2]
        
        # Get target answer
        target = puzzle.get('answer', puzzle.get('target', 0))
        if isinstance(target, str):
            # Convert letter answer to index (A=0, B=1, etc.)
            if target.upper() in 'ABCD':
                target = ord(target.upper()) - ord('A')
            else:
                try:
                    target = int(target)
                except:
                    target = 0
        
        # Get puzzle ID
        puzzle_id = puzzle.get('id', puzzle.get('puzzle_id', puzzle.get('question_id', str(hash(str(puzzle))))))
        
        return {
            'puzzle_id': puzzle_id,
            'question': clean_question,
            'options': options,
            'target': target,
            'images': images,
            'metadata': {
                'category': puzzle.get('category', ''),
                'subcategory': puzzle.get('subcategory', ''),
                'id': puzzle_id,
                'all_data': puzzle
            }
        }
        
    except Exception as e:
        print(f"ERROR in format_puzzle: {e}")
        return None
