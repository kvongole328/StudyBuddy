import openai
import os 
def generate_response(input_string):
    # Set the API key
    openai.api_key = os.environ["OPEN_AI_KEY"]


    # Set the model to use
    model = "text-davinci-003"

    # Set the prompt to use as input

    # Use the `Completion` API to generate a response to the prompt
    response = openai.Completion.create(
        engine=model,
        prompt=input_string,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5
    )

    # Print the generated response
    
    print(response['choices'][0]['text'])
    return(response['choices'][0]['text'])