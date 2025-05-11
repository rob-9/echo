import google.generativeai as genai
from typing import List, Dict, Any
import os

class AIBriefingSystem:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.conversation_history = []
        
    def get_next_question(self, user_input: str = None) -> str:
        """Get the next question to ask the user based on the conversation history."""
        if user_input:
            self.conversation_history.append({"role": "user", "content": user_input})
        
        # Create a prompt that guides the conversation
        prompt = """You are an AI assistant helping to gather requirements for a design project. 
        Your goal is to ask relevant questions to understand the client's needs.
        Start with broad questions and gradually get more specific.
        Focus on understanding:
        1. The overall purpose and goals
        2. Target audience
        3. Style preferences
        4. Specific requirements
        5. Any constraints or limitations
        
        Based on the conversation history, what is the next most relevant question to ask?
        Keep your response concise and focused on a single question."""
        
        # Add conversation history to the prompt
        if self.conversation_history:
            prompt += "\n\nPrevious conversation:\n"
            for msg in self.conversation_history:
                prompt += f"{msg['role']}: {msg['content']}\n"
        
        response = self.model.generate_content(prompt)
        question = response.text.strip()
        self.conversation_history.append({"role": "assistant", "content": question})
        return question
    
    def generate_images(self, prompt: str) -> List[str]:
        """Generate images based on the gathered requirements."""
        # Create a detailed prompt for image generation
        image_prompt = f"""Based on the following requirements, generate a detailed description for an image:
        {prompt}
        
        Focus on:
        1. Visual style and aesthetics
        2. Key elements and composition
        3. Color scheme and mood
        4. Technical specifications
        
        Provide a detailed description that can be used to generate an image."""
        
        response = self.model.generate_content(image_prompt)
        image_description = response.text.strip()
        
        # Here you would integrate with an image generation API
        # For now, we'll return placeholder URLs
        # TODO: Replace with actual image generation
        return ["placeholder_image_url_1", "placeholder_image_url_2"]
    
    def get_feedback(self, image_url: str, feedback: str) -> str:
        """Process user feedback on generated images and suggest improvements."""
        prompt = f"""The user provided the following feedback on the generated image:
        {feedback}
        
        Based on this feedback and our previous conversation, what specific improvements should we make?
        Focus on actionable changes that can be implemented."""
        
        response = self.model.generate_content(prompt)
        return response.text.strip() 