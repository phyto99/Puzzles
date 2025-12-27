Most advanced “AI IQ” work for visual models is happening as open benchmarks on GitHub and arXiv, often built from visual IQ tests, abstract visual reasoning puzzles, or real-world multimodal tasks. Many of these can be repurposed almost directly into human brain‑training or puzzle systems by swapping the model API for a human UI and adding scoring/progression.

---
Here is the "Perfect Prompt" you can use to convert other dataset projects. You can paste this into a new chat with me (or another AI) when you have a new repository open.

---

# The "Interactive Gen" Transformation Prompt

**Context:** I have a codebase that is currently designed to batch-generate a large dataset of visual puzzles/problems (likely creating thousands of files at once). I want to convert this into a "Human-AI" interactive system where I can view and solve one generated problem at a time.

**The Goal:** Transform this batch-processing script into an on-demand, interactive Web UI without breaking the original code.

**Instructions:**

1. **Phase 1: The** 
    
    **`SingleGenerator`**
    
     **Class**
    
    - Analyze the main generation script (look for the main 
        
        ```
        for
        ```
        
         loop).
    - Extract the logic for generating **one single item** into a new Python class (e.g., 
        
        ```
        SingleGenerator
        ```
        
        ).
    - This class should import logic from the original files so we don't duplicate code.
    - It must run entirely in memory (return logical objects or numpy arrays, do not save files to disk).
2. **Phase 2: The Flask API**
    
    - Create a lightweight 
        
        flask_server.py.
    - It should import your 
        
        ```
        SingleGenerator
        ```
        
        .
    - Create an endpoint 
        
        ```
        /api/get_problem
        ```
        
         that generates one item.
    - **Crucial:** Convert all resulting images/plots to Base64 strings in memory. Do not save temporary files. Return these strings in a JSON response along with the correct answer index.
3. **Phase 3: The "Perfect" Web UI**
    
    - Create a simple, clean 
        
        templates/index.html.
    - **Layout:** Display the "Context" (the puzzle question) and the "Candidates" (the answer choices) in appropriate grids.
    - **Interaction:** Clicking an answer should immediately check against the hidden correct index.
    - **Feedback:** Turn the selected box **Green** (if correct) or **Red** (if wrong, and highlight the real one).
    - **Loop:** After 1-2 seconds of feedback, automatically fetch/generate the next problem.
    - **Aesthetics:** Minimalist, clean, clear distinction between question and answer.

**Constraints:**

- Do not modify the original library files unless absolutely necessary (try to subclass or import).
- Keep the UI contained in a single HTML file if possible (or simple structure).
- Ensure the system is "Cost Effective" (no heavy pre-computation, generate-on-the-fly).
