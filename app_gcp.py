import google.auth
import google.genai as genai
from google.genai import types
import json

# Initialize the GenAI client
def get_genai_client():
    """Initialize and return a GenAI client"""
    client = genai.Client(
        vertexai=True,
        project="arcane-shape-449219-v0",  # Set your Google Cloud project ID
        location="us-central1",            # Set the location, e.g., us-central1
    )
    return client


# Function to create a structured prompt from user data for the healthcare checklist
def create_healthcare_checklist_prompt(user_data):
    """Create a structured prompt from user data for the healthcare checklist"""
    concerns = user_data.get('concerns', '')
    conditions = user_data.get('conditions', '')
    medications = user_data.get('medications', '')

    # Create a more detailed patient profile for better context
    patient_profile = f"""
    - Height: {user_data.get('height')}
    - Weight: {user_data.get('weight')}
    - Age: {user_data.get('age')}
    - Location: {user_data.get('location')}
    - Ethnicity: {user_data.get('ethnicity')}
    - Pre-existing conditions: {conditions if conditions else 'None reported'}
    - Health concerns: {concerns if concerns else 'None specified'}
    - Current medications and supplements: {medications if medications else 'None reported'}
    """

    return f"""
    Create a compassionate, personalized healthcare appointment checklist for a patient with the following characteristics:
    {patient_profile}

    Provide a structured checklist in JSON format with the following sections:
    1. "introduction": A brief, empathetic message acknowledging the patient's situation and concerns (2-3 sentences)
    2. "pre_appointment": A list of questions for the patient to consider BEFORE the appointment (about preparations, documents to bring, information to gather)
    3. "during_appointment": A list of questions for the patient to ask DURING the appointment (4-6 thoughtful, personalized questions based on specific conditions and concerns)
    4. "post_appointment": A list of questions about follow-up items and next steps AFTER the appointment
    5. "emotional_support": Brief supportive message to help reduce anxiety about the appointment (1-2 sentences)

    For all sections, ensure the content is formatted as questions rather than statements.
    For example, instead of "Bring your insurance card", use "Have you packed your insurance card?"

    The questions should consider:
    - The patient's specific conditions and how they might be progressing or managed
    - Age-appropriate health concerns and preventative measures
    - Medication interactions or side effects if medications are listed
    - Regional or ethnic-specific health considerations when relevant
    - Addressing any specific concerns they've mentioned

    Ensure all advice is personalized to their specific situation rather than generic medical advice.
    """

# Update the function to handle the raw response and debug the output
def generate_healthcare_checklist(user_data):
    client = get_genai_client()

    prompt = create_healthcare_checklist_prompt(user_data)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ]

    # Set up the content generation configuration
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="OFF"
            ),
        ],
    )

    # Request the content generation from the model
    result = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.0-flash-001",
        contents=contents,
        config=generate_content_config,
    ):
        result += chunk.text

    # Debug: Print the raw response to check if it's valid JSON
    print("Raw Response:", result)

    try:
        # Attempt to parse the response as JSON
        formatted_checklist = json.loads(result)  # Convert to a Python dictionary
        pretty_checklist = json.dumps(formatted_checklist, indent=2)  # Format with indent for readability
        return pretty_checklist
    except json.JSONDecodeError as e:
        # If JSON parsing fails, print the error and return the raw response
        print(f"Error parsing JSON: {e}")
        return {"error": "Could not generate a valid checklist", "raw_response": result}
