"""must pip install requests once"""

import logging
import openai
import pandas as pd
import csv
from datetime import datetime
import os
import html
import requests
import json
import threading
import importlib
import re    
dookery = importlib.import_module('dookery')

"""********************************GLOBALS************************************************"""
# Set File paths
skudf_file_path = r"C:\\Users\\LittleChickpea\\Downloads\\SKU_Checklist.csv"
skujson_file_path = "C:\\Users\\LittleChickpea\\Downloads\\Logs\\SKU_Checklist.json"
productlisting_file_path = r"C:\\Users\\LittleChickpea\\Downloads\\Productlisting.csv"
productlistingjson_file_path = r"C:\\Users\\LittleChickpea\\Downloads\\Productlisting.json"
threaddf_file_path = r"C:\\Users\\LittleChickpea\\Downloads\\thread_library.csv"

# Initialize a lock for threading safety
threaddf_lock = threading.Lock()
prodf_lock = threading.Lock()
skudf_lock = threading.Lock()
logging_lock = threading.Lock()
api_call_lock = threading.Lock()

# Set OpenAI API variables (constant throughout the script)
openai_api_key = os.getenv("OPENAI_API_KEY", None)
organization_id = os.getenv("ORGANIZATION_ID", None)
project_id = os.getenv("PROJECT_ID", None)
m_assistant_id = "asst_JXUSnRujRuSUjc9VSiACX13B"
base_url = "https://api.openai.com/v1"

# Generate a filename with the current datetime for script logging
log_filename = datetime.now().strftime("automation_%Y-%m-%d_%H-%M-%S.log")
log_file_path = os.path.join("C:\\Users\\LittleChickpea\\Downloads\\Logs", log_filename)
print(f"Log file will be: {log_filename}")

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Manually create the log file if it doesn't exist
# if not os.path.exists(log_file_path):
#    with open(log_file_path, 'w') as f:
#        pass  # Just open and close the file to create it
# Configure logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)  # Explicitly set the logger level to INFO

# Configure logging
logging.basicConfig(
    handlers=[logging.FileHandler(log_file_path, 'a', 'utf-8')],
    #filename='test.log',
    level=logging.DEBUG,
    force=True,
    format='%(asctime)s:%(levelname)s:%(message)s'
)
print(f"Logging: {logging}")
# logger.info("LOGGER INFO TEST Logging successfully initialized.")
logging.info("LOGGING INFO TEST Logging successfully initialized.")
print("Logging successfully initialized.")

"""********************************MAP VARIABLES******************************************"""
# Tools variable
tools = [
    {
        "type": "code_interpreter",
        "function": ""  # Add the appropriate function if required
    },
    {
        "type": "file_search",
        "function": ""  # Add the appropriate function if required
    }
]

"""********************************FUNCTIONS*************************************************************"""
# Initilise OPENAI 
def initialize_client():
    from openai import OpenAI
    # local_client = openai.OpenAI()
    with api_call_lock:
        local_client = OpenAI(api_key=openai_api_key)
    with logging_lock:
        logging.info(f"\n Successfully set {local_client}")   
    print(f"\n Successfully set {local_client}")   
    return local_client

def updatedataframe(prodf, count, entryName, entryResult, productlisting_file_path):
    try:
        print("\n Updating DataFrame to open CSV file...")
        print(f"prodf: {prodf}")
        with logging_lock:
            logging.info(f"\n Updating DataFrame to open CSV file... \n {prodf}")

        with prodf_lock:
            prodf.loc[count, entryName] = entryResult

        # Save the updated DataFrame to CSV
        prodf.to_csv(productlisting_file_path, index=False, encoding='utf-8')

        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"Successfully saved {entryName} CSV at {currentDateTime} : {entryResult}")
        with logging_lock:
            logging.info(f"Successfully saved {entryName} CSV at {currentDateTime} : {entryResult}")

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"Failed to save CSV at {currentDateTime}: {str(e)}")
        with logging_lock:
            logging.error(f"Failed to save CSV at {currentDateTime}: {str(e)}")

# Function to check marketing personality variable against the Marketing Personality attached to the assistant and update if there's a discrepancy
def check_and_update_marketing_personality(m_assistant_id, marketing_personality, client):
    try:
        # Retrieve the current marketing personality from the assistant
        with api_call_lock:
            assistant_details = client.beta.assistants.retrieve(m_assistant_id)
            current_personality = assistant_details.metadata.get("marketing_personality", None)

        with logging_lock:
            logging.info(f"\n def check_and_update_marketing_personality: Assistant Details: {assistant_details}")
        print(f"\n def check_and_update_marketing_personality: Assistant Details: {assistant_details}")

        # Check if the current personality matches the predefined one
        if current_personality != marketing_personality:
            print("Discrepancy found in marketing personality. Updating assistant...")
            with api_call_lock:
                updated_assistant = client.beta.assistants.update(
                    m_assistant_id,
                    instructions=marketing_personality,
                )
            print("Marketing personality updated successfully.")
            with logging_lock:
                logging.error(f"{marketing_personality}")
        else:
            print("Marketing personality is up-to-date.")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to check or update marketing personality at {currentDateTime}: {str(e)}")
        print(f"Failed to check or update marketing personality at {currentDateTime}: {str(e)}")
        raise
 
# Load and prepare a CSV file, must set file path and file description first 
def load_and_prepare_csv(file_path, file_description):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_description} file not found: {file_path}")

        with logging_lock:
            logging.info(f"\n def load_and_prepare_csv: Loading the {file_description} CSV...")
        print(f"\n def load_and_prepare_csv: Loading the {file_description} CSV...")

        # Choose the appropriate lock based on the file being processed
        if "SKU_Checklist" in file_description:
            with skudf_lock:
                df = pd.read_csv(file_path, encoding='utf-8')
        elif "Product Listing" in file_description:
            with prodf_lock:
                df = pd.read_csv(file_path, encoding='utf-8')
        elif "Thread Library" in file_description:
            with threaddf_lock:
                df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_csv(file_path, encoding='utf-8')  # Default case

        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.info(f"Successfully loaded {file_description} CSV file at {currentDateTime} with {len(df)} records.")
        print(f"Successfully loaded {file_description} CSV file")
        return df

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to load {file_description} CSV file at {currentDateTime}: {str(e)}")
        print(f"Failed to load {file_description} CSV file")  # Debugging print statement
        raise
    
# Extract SKU_data from the DataFrame (only applies to sku_checklist)
def extract_sku_data(skudf):
    try:
        with skudf_lock:
            sku_checklist = skudf['SKU'].tolist()
        with logging_lock:
            logging.info(f"\n def extract_sku_data: Extracted {len(sku_checklist)} SKUs from sku_checklist.")
        print(f"\n def extract_sku_data: Extracted {len(sku_checklist)} SKUs from sku_checklist.")

        # Convert SKU column to string explicitly (this is just an extra safety measure)
        with skudf_lock:
            skudf['SKU'] = skudf['SKU'].apply(lambda x: str(x).strip())
        print("Converting SKUs to string...")
        with logging_lock:
            logging.info("Converting sku_checklist variable to string.")        
        
        # Set sku_checklist variable
        sku_checklist = set(sku_checklist)
        print(sku_checklist)
        with logging_lock:
            logging.info("sku_checklist variable set successfully.")
        return sku_checklist
    
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to extract data from sku_checklist at {currentDateTime}: {str(e)}")
        print("Failed to extract data from sku_checklist")
        raise
    
# Convert DataFrame to JSON format
def convert_to_json(df):
    try:
        with skudf_lock:
            json_output = df.to_json(orient='records', lines=True)
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.info(f"\n def convert_to_json: Successfully converted dataframe to JSON at {currentDateTime}")
        print("\n def convert_to_json: Successfully converted dataframe to JSON")
        return json_output
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to convert dataframe to JSON at {currentDateTime}: {str(e)}")
        print("Failed to convert dataframe to JSON")
        raise

# Save JSON output to a file 
def save_json_to_file(json_output, json_file_path):
    try:
        with logging_lock:
            with open(json_file_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            logging.info(f"\n def save_json_to_file: JSON file saved successfully to {json_file_path}.")
        print(f"\n def save_json_to_file: JSON file saved successfully to {json_file_path}.")
    
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"\n Failed to save JSON file at {currentDateTime}: {str(e)}")
        print("\n Failed to save JSON file")
        raise

def update_and_save_csv(file_path, df):
    try:
        # Print df to check its type
        print(type(df))
        
        # Save the DataFrame to a CSV file
        with prodf_lock:
            df.to_csv(file_path, index=False, encoding='utf-8')
        with logging_lock:
            logging.info(f"\n def update_and_save_csv: CSV file updated and saved successfully to {file_path}.")
        print(f"\n def update_and_save_csv: CSV file updated and saved successfully to {file_path}.")        
    except Exception as e:
        print(f"Error: {e}")
        with logging_lock:
            logging.error(f"Failed to save DataFrame to CSV at {file_path}: {str(e)}")
        raise

def isProductSKUInChecklist(sku_checklist, count, productSKU, productName, productType):
    try:
        if productSKU in sku_checklist:
            with logging_lock:
                logging.info(f"\n def isProductSKUInChecklist: SKU {productSKU} already processed, skipping.")
            print(f"\n def isProductSKUInChecklist: SKU {productSKU} already processed, skipping.")
            return True
        
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.info(f"Commencing product processing {count + 1}: {productName} at {currentDateTime}")
        print(f"Successfully commenced processing product {productSKU} {count + 1}: {productName} at {currentDateTime}")
    
    except Exception as e:
        # Log any errors that occur during the processing of this product
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to process product {count + 1} at {currentDateTime}: {str(e)}")
        print(f"Error processing product {count + 1} at {currentDateTime}: {str(e)}")
        return

# Function to find the parent/variable SKU by checking current product SKU for parent variable then reading backwards through the product list.
def find_parent_sku(productType, productSKU, prodf, current_index):
    try:
        with logging_lock:
            logging.info("\n def find_parent_sku: Finding Parent SKU...")
        print("\n def find_parent_sku: Finding Parent SKU...")
        
        if productType == 'variable':
            print(f"Product is type {productType}, so Parent SKU is set to: {productSKU}")
            with logging_lock:
                logging.info(f"Product is type {productType}, so Parent SKU is set to: {productSKU}")
            return productSKU
        else:
            # If not variable product, search for Parent SKU
            with logging_lock:
                logging.info("Searching for Parent SKU by checking previous rows...")
            print("Searching for Parent SKU by checking previous rows...")
            
            with prodf_lock:
                for i in range(current_index, -1, -1):  # Start from current_index and go upwards
                    if pd.notna(prodf.iloc[i]['SKU']) and prodf.iloc[i]['Type'].lower() == "variable":
                        parent_sku = prodf.iloc[i]['SKU']
                        
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        with logging_lock:
                            logging.info(f"Successfully obtained Parent_SKU {parent_sku} at {currentDateTime}")
                        print(f"Successfully obtained Parent_SKU {parent_sku} at {currentDateTime}")                    
                            
                        return parent_sku  # Return the parent SKU once found
                    print("No Parent SKU found above the current index.")
                    
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to obtain Parent_SKU at {currentDateTime}: {str(e)}")
        print(f"Failed to obtain Parent_SKU at {currentDateTime}: {str(e)}")
        raise                    

# Function to find all sibling/children/variant SKUs by reading forward from the Parent/variable in productlistings.csv to the next parent/variable
def get_children_skus(parent_sku, prodf, start_index):
    try:
        with logging_lock:
            logging.info(f"\n def get_children_skus: Finding Children SKUs for Parent SKU: {parent_sku}...")
        print(f"\n def get_children_skus: Finding Children SKUs for Parent SKU: {parent_sku}...")

        children_skus = []
        parent_sku_found = False

        # Iterate through the DataFrame
        with prodf_lock:
            for i in range(start_index, len(prodf)):
                # Ensure the SKU and Type columns are not NaN
                sku = prodf.iloc[i, 0]
                product_type = prodf.iloc[i, 1]
                
                if pd.notna(sku) and pd.notna(product_type):
                    # Check if the current row matches the parent SKU
                    if sku == parent_sku:
                        parent_sku_found = True
                        print(f"Parent SKU {parent_sku} found at index {i}")
                    elif parent_sku_found and product_type.lower() == "variable":
                        print(f"Next variable SKU found at index {i}, stopping search.")
                        break  # Stop when the next variable entry is found
                    elif parent_sku_found and product_type.lower() == "variation":
                        children_skus.append(sku)  # Append the SKU to children_skus if it's a variation
                        print(f"Child SKU {sku} found at index {i}")
                        with logging_lock:
                            logging.info(f"Child SKU {sku} found at index {i}")
        
        # Log the children SKUs obtained
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.info(f"Successfully obtained Children_SKUs {children_skus} at {currentDateTime}") 
        print(f"Successfully obtained Children_SKUs {children_skus} at {currentDateTime}")
                    
        return children_skus
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to obtain Children_SKUs at {currentDateTime}: {str(e)}")
        print(f"Failed to obtain Children_SKUs at {currentDateTime}: {str(e)}")
        raise

# Function to upload a file to an assistant
def upload_file(file_path, client):
    try:
        # Open and upload the file
        with open(file_path, "rb") as file:
            with api_call_lock:
                response = client.files.create(
                    file=file,
                    purpose='assistants'
                )
        # Log and print the response
        file_id = response['id']
        with logging_lock:
            logging.info(f"\n def upload_file: File uploaded successfully. File ID: {file_id}")
        print(f"\n def upload_file: File uploaded successfully. File ID: {file_id}")
        return file_id
    except Exception as e:
        with logging_lock:
            logging.error(f"Failed to upload file: {e}")
        print(f"Failed to upload file: {e}")
        raise


# Function to create an Assistant with the code_interpreter tool enabled and provide the file as a resource to the tool
def create_assistant(assistant_name, assistant_description, file_id, client):
    try:
        # Create the assistant
        with api_call_lock:
            assistant = client.beta.assistants.create(
                name=assistant_name,
                description=assistant_description,
                model="gpt-4o",
                tools=[{"type": "code_interpreter"}],
                tool_resources={
                    "code_interpreter": {
                        "file_ids": [file_id]
                    }
                }
            )
        # Log and print the response
        assistant_id = assistant['id']
        with logging_lock:
            logging.info(f"\n def create_assistant: Assistant created successfully. Assistant ID: {assistant_id}")
        print(f"\n def create_assistant: Assistant created successfully. Assistant ID: {assistant_id}")
        return assistant_id
    except Exception as e:
        with logging_lock:
            logging.error(f"Failed to create assistant: {e}")
        print(f"Failed to create assistant: {e}")
        raise
    
# Function to handle threading logic and set current Thread_ID
def threading_logic(productSKU, parent_sku, df, client):
    if not parent_sku:
        raise ValueError("No Parent SKU provided. Cannot proceed without a Parent SKU.")

    # Initialize thread_id with a default value
    thread_id = None  # Default value, adjust as necessary

    # Initialize the OpenAI client
    with api_call_lock:
        openai.api_key = openai_api_key
    
    print(f"\n def threading_logic: Initialized OpenAI client with provided API key for processing SKU: {productSKU}")
    with logging_lock: 
        logging.info(f"\n def threading_logic: Initialized OpenAI client with provided API key for processing SKU: {productSKU}\n")

    try:
        print(f"\n Processing Parent SKU {parent_sku} for Product SKU {productSKU}...")
        with logging_lock: 
            # Logging the start of processing
            logging.info(f"\n Processing Parent SKU {parent_sku} for Product SKU {productSKU}...")   
            
        # Search for parent_sku in the thread library list with improved safety checks
        with threaddf_lock:
            existing_entry = df[(df['parent_sku'] == parent_sku) & (df['productSKU'] == productSKU)]
            
        print(f"Thread ID retrieved: {thread_id}, attempting to retrieve parent thread...")
        with logging_lock: 
            logging.info(f"Thread ID {thread_id} found for Parent SKU {parent_sku}")
            
        
        if not existing_entry.empty:
            # Existing thread found, retrieve the thread_id
            thread_id = existing_entry['thread_id'].iloc[0]
            
            print(f"Thread ID retrieved: {thread_id}")
            with logging_lock: 
                logging.info(f"Thread ID {thread_id} found for Parent SKU {parent_sku}")

            # Retrieve thread immediately
            with api_call_lock:
                my_thread = client.beta.threads.retrieve(thread_id)
                thread_id = my_thread.id
            
            print(f"Retrieved thread details for Parent SKU {parent_sku}: {thread_id}")
            with logging_lock: 
                logging.info(f"Retrieved thread details for Parent SKU {parent_sku}: {thread_id}")
                                        
        else:
            print(f"No existing Thread ID found for Parent SKU {parent_sku}. Creating new thread...")
            with logging_lock: 
                logging.warning(f"No existing Thread ID found for Parent SKU {parent_sku}. Creating new thread...")

            # Create thread if no parent sku entry in threaddf
            with api_call_lock:
                new_thread = client.beta.threads.create()
                thread_id = new_thread.id
            
            print(f"Created new thread for Product SKU {productSKU} using Parent SKU {parent_sku}: {thread_id}") 
            with logging_lock: 
                logging.info(f"Created new thread for Product SKU {productSKU} using Parent SKU {parent_sku}: {thread_id}")

            
            # Update Threaddf with new information
            new_entry = pd.DataFrame({'productSKU': [productSKU], 'parent_sku': [parent_sku], 'thread_id': [thread_id]})
            with threaddf_lock:
                df = pd.concat([df, new_entry], ignore_index=True)
            
            print(f"\n Updated ThreadDF for thread ID: {thread_id}") 
            with logging_lock:
                logging.info(f"\n Updated ThreadDF for SKU {productSKU} with Thread ID {thread_id}")

    except Exception as e:
        print(f"Error in threading logic: {str(e)}")
        with logging_lock: 
            logging.error(f"Failed in threading logic for SKU {productSKU}: {str(e)}")
        raise e
    
    return df, thread_id

# Function to get parent information to attach to the message
def extractedparentinfo(parent_sku, DFObject, prodf):
    try:
        with prodf_lock:
            # Find the row that matches SKU to the variable parent_sku and checks Type is 'variable'
            parent_row = prodf[(prodf['SKU'] == parent_sku) & (prodf['Type'].str.lower() == 'variable')]
        
            # If the parent_row is found, extract the Parent's xxx info
            if not parent_row.empty:
                extractedparentinfo = parent_row.iloc[0][DFObject]
                print(f"\n Sourced {DFObject} information using Parent SKU: {parent_sku} at index {parent_row.index[0]}")
                logging.info(f"\n Sourced {DFObject} information using Parent SKU: {parent_sku} at index {parent_row.index[0]}")
                return extractedparentinfo  # Corrected the return statement to return the correct variable

    except Exception as e:
        print(f"Error sourcing parent information: {str(e)}")
        raise

# Function to clean and sanitize a CSV extraction
def sanitize_description(description):
    # Check for NaN values and replace with an empty string
    if pd.isna(description):
        return ''
    
    # HTML Decoding
    description = html.unescape(description)

    # Convert description to string if it's not already
    description = str(description)
    
    # Remove any unnecessary backslashes
    description = description.replace("\\", "")
    
    # Remove HTML tags but preserve '>'
    description = re.sub(r'<[^>]*>', '', description)
    
    # Remove markdown or any surrounding quotes and ``` 
    description = re.sub(r'[`"\']+', '', description)
    
    # Remove the word 'json' if it appears
    description = re.sub(r'\bjson\b', '', description, flags=re.IGNORECASE)
    
    # Remove the word 'Categories' if it appears
    description = re.sub(r'\bCategories\b', '', description, flags=re.IGNORECASE)
    
    # Remove square brackets and colons
    description = description.replace("[", "").replace("]:", "")
    
    # Remove extra whitespace and newlines
    description = re.sub(r'\s+', ' ', description).strip()
    
    # Ensure proper comma separation
    description = re.sub(r' *, *', ', ', description)
    
    # Log the sanitization process
    logging.info("\n Sanitizing information...")
    print("\n Sanitizing information...")
    
    return description

# Function to generate xxx using the getChatCompletions function
def getChatCompletions(openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client):
    try:
        print("\n def getChatCompletions: \n Starting chat completion process...")
        with logging_lock:
            logging.info("\n def getChatCompletions: \n Starting chat completion process...\n")

        if productSKU == parent_sku:
            response = responseParentProduct
            print(f"Requesting generation with the following prompt: \n {response} TO REPLACE {xxx}")
            with logging_lock:
                logging.info(f"Requesting generation with the following prompt: \n {response} TO REPLACE {xxx}")

        else:
            response = responseChildProduct
            print(f"Requesting generation with the following prompt: \n {response} TO REPLACE {xxx}")
            with logging_lock:
                logging.info(f"Requesting generation with the following prompt: \n {response} TO REPLACE {xxx}")
            
        # Step 1: Create a Thread Message
        with logging_lock:
            logging.info(f"\n STEP ONE: Creating thread message...")
        with api_call_lock:
            thread_message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=response,
            )
        print(f"STEP ONE: Thread message created: {thread_message}")
        with logging_lock:
            logging.info("STEP ONE: Successfully created thread message.")

        # Step 2: Create a Run
        with logging_lock:
            logging.info(f"\n STEP TWO: Creating run...")
        with api_call_lock:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=m_assistant_id
            )
        print(f"STEP TWO: Run created...")
        print(f"STEP TWO: Run ID: {run.id}")

        # Poll run for completion status 
        if run.status == 'completed':
            with logging_lock:
                logging.info("STEP TWO: Run status complete...")
            print("STEP TWO: Run status complete...")
            
            with api_call_lock:
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id
                )
            print(messages)
            with logging_lock:
                logging.info(f"STEP TWO: Successfully created run. Run ID: {run.id}")
            print(f"STEP TWO: Successfully created run. Run ID: {run.id}")
        else:
            print(f"Run failed with status: {run.status}")
            
            # Attempt to retrieve error message
            if hasattr(run, 'error'):
                print(f"Run error: {run.error}")
                with logging_lock:
                    logging.error(f"Run failed with error: {run.error}")
            else:
                print("Run failed without error message.")
                with logging_lock:
                    logging.error("Run failed without error message.")
            raise Exception(f"Run failed with status: {run.status}")

        # Step 3: List Run Steps
        print("STEP THREE: Listing run steps...")
        with logging_lock:
            logging.info("STEP THREE: Listing run steps...")
            
        with logging_lock:
            logging.info("IF IT FAILS HERE: YOU'VE RUN OUT OF OPENAI CREDITS, DUMBASS!!!")
            
        with api_call_lock:
            run_steps = client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run.id
            )
        print(f"STEP THREE: Run steps: {run_steps}. RUN STEPS SUCCESS.")
        with logging_lock:
            logging.info(f"STEP THREE: Successfully listed {run_steps} for Run ID: {run.id}")
            print(f"STEP THREE: Successfully listed {run_steps} for Run ID: {run.id}")

        # Step 4: Extract Message IDs from Run Steps
        message_ids = []
        for run_step in run_steps:
            logging.info(f"STEP FOUR: Run step data: {run_step}")
            print(f"STEP FOUR: Run step data: {run_step}")
            
            if run_step.type == 'message_creation':
                message_ids.append(run_step.step_details.message_creation.message_id)
                logging.info(f"STEP FOUR: Extracted 'message creation' message IDs: {message_ids}")
        print(f"STEP FOUR: Extracted 'message creation' message IDs: {message_ids}")

        # Step 5: Retrieve Messages and Compile Responses
        response_content = []
        for msg_id in message_ids:
            with api_call_lock:
                message = client.beta.threads.messages.retrieve(
                    message_id=msg_id,
                    thread_id=thread_id
                )
            logging.info(f"STEP FIVE: Retrieved message: {message}")
            print(f"STEP FIVE: Retrieved message: {message}")
            with logging_lock:
                logging.info(f"STEP FIVE: Retrieved message: {message}")
                print(f"STEP FIVE: Retrieved message: {message}")
            response_text = message.content[0].text.value
            response_content.append(response_text)

        # Step 6: Combine all responses into a single string
        final_response = " ".join(response_content)
        
        with logging_lock:
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"STEP SIX: Final compiled response: {final_response}")
        print(f"STEP SIX: Final compiled response: {final_response}")
        
        with logging_lock:
            logging.info("Successfully generated response.")
        print("Successfully generated response.")     

        return final_response
    
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed during chat completion process at {currentDateTime}: {str(e)}")
        print(f"Failed during chat completion process at {currentDateTime}: {str(e)}")
        raise
    
# Function to get a chat completion from openai:
def genChatCompletions(requestMessageContent):
    with api_call_lock:
        responseName = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"{marketingPersonality} {requestMessageContent}"}
            ]
        )
    with logging_lock:
        logging.info(f"\n def genChatCompletions: {requestMessageContent}")
    print(f"\n def genChatCompletions: {requestMessageContent}")
    return responseName.choices[0].message.content
    
    """********************************BEGIN_SCRIPTING***********************************"""
def main(skudf_file_path, skujson_file_path, productlisting_file_path, threaddf_file_path, productlistingjson_file_path, openai_api_key, organization_id, project_id, base_url, marketing_personality, category_map, tag_map, attributes_map, logging, logging_lock):

    # Commence Product Listing script
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with logging_lock:
        logging.info(f"\n Script started at {currentDateTime}.")
    print(f"\n Script started at {currentDateTime}.")
    with logging_lock:
        logging.info("def main(skudf_file_path, skujson_file_path, productlisting_file_path, threaddf_file_path, productlistingjson_file_path, openai_api_key, organization_id, project_id, base_url, marketing_personality, category_map, logging, logging_lock)")
    
    # Initialize the OpenAI client
    with api_call_lock:
        openai.api_key = openai_api_key
    client = initialize_client()

    # Set Marketing Assistant_ID
    m_assistant_id = "asst_JXUSnRujRuSUjc9VSiACX13B"
    
    # Ensure OpenAI API key is set
    if not openai_api_key:
        raise ValueError("OpenAI variables not found in environment variables.")    

    # Read CSV files into DataFrames
    try:
        with prodf_lock:
            # Define dtype_dict
            dtype_dict = {
                'Type': str,
                'SKU': str,
                'Name': str, 
                'Short description': str,
                'Description': str, 
                'Weight (kg)': str,
                'Length (cm)': str,
                'Width (cm)': str,
                'Height (cm)': str, 
                'Purchase note': str,
                'Categories': str,
                'Tags': str, 
                'Shipping class': str, 
                'Images': str, 
                'Upsells': str, 
                'Cross-sells': str,
                'Attribute 1 name': str, 
                'Attribute 1 value(s)': str, 
                'Attribute 2 name': str, 
                'Attribute 2 value(s)': str,
                'Attribute 3 name': str,
                'Attribute 3 value(s)': str,
            }

            # Read the CSV with specified data types
            prodf = pd.read_csv(
                productlisting_file_path,
                encoding='utf-8',
                dtype=dtype_dict
            )

            # Get the list of string columns
            string_columns = list(dtype_dict.keys())

            # Fill NaN values with empty strings for string columns
            prodf[string_columns] = prodf[string_columns].fillna('')
            
            print(prodf.dtypes)
            logging.info(prodf.dtypes)
            
        with skudf_lock:
            skudf = pd.read_csv(skudf_file_path, encoding='utf-8')
        with threaddf_lock:
            threaddf = pd.read_csv(threaddf_file_path, encoding='utf-8')
        with logging_lock:
            logging.info("Successfully loaded CSV files into DataFrames.")
    except Exception as e:
        with logging_lock:
            logging.error(f"\n Failed to load CSV files: {str(e)}")
        raise
    
    # Function to check and update the marketing personality        
    check_and_update_marketing_personality(m_assistant_id, marketing_personality, client)
    
    # Load SKU Checklist
    skudf = load_and_prepare_csv(skudf_file_path, "SKU Checklist")
    
    # Extract SKU data and convert to JSON
    sku_checklist = extract_sku_data(skudf)
    json_output = convert_to_json(skudf)
    save_json_to_file(json_output, skujson_file_path)  
    
    # Load Product Listing
    prodf = load_and_prepare_csv(productlisting_file_path, "Product Listing")

    # Get the total number of products in the Productlistings dataframe
    prodfLength = len(prodf)
    count = 0
    
    # Loop through each row in the DataFrame to process product listings
    for count, row in prodf.iterrows():
        try:
            logging.info("\n Looping through the DataFrame...")
            print(f"\n Processing product {count + 1}...")
            logging.info(f"Processing product {count + 1}...")

            # Ensure the loop runs within bounds of the DataFrame
            if count <= prodfLength - 1:
                productUID = row['ID']
                productType = row['Type']
                productSKU = row['SKU']
                productName = row['Name']
                productPublished = row['Published']
                productFeatured = row['Is featured?']
                productSDescription = row['Short description']
                productLDescription = row['Description']
                productWeight = row['Weight (kg)']
                productLength = row['Length (cm)']
                productWidth = row['Width (cm)']
                productHeight = row['Height (cm)']
                productReviews = row['Allow customer reviews?']
                productPurchaseNote = row['Purchase note']
                productPrice = row['Regular price']
                productCategories = row['Categories']
                productTags = row['Tags']
                productShippingClass = row['Shipping class']
                productImages = row['Images']
                productUpsell = row['Upsells']
                productCross = row['Cross-sells']
                productAttributeOneName = row['Attribute 1 name']
                productAttributeOneDesc = row['Attribute 1 value(s)']
                productAttributeTwoName = row['Attribute 2 name']
                productAttributeTwoDesc = row['Attribute 2 value(s)']
                productAttributeThreeName = row['Attribute 3 name']
                productAttributeThreeDesc = row['Attribute 3 value(s)']
                
                # Handle NaN values
                if pd.isna(productLDescription):
                    productLDescription = ''                    
                    
                # Sanitize descriptions
                productLDescription = sanitize_description(productLDescription)
                productSDescription = sanitize_description(productSDescription)
                
                # Process product and update checklist                
                if not isProductSKUInChecklist(sku_checklist, count, productSKU, productName, productType):
                    # Get Parent SKU
                    try:
                        current_index = count
                        parent_sku = find_parent_sku(row['Type'], row['SKU'], prodf, current_index)
                    except Exception as e:
                        with logging_lock:
                            logging.error(f"\n Failed to obtain Parent_SKU at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}: {e}")
                        print(f"\n Failed to obtain Parent_SKU at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}: {e}")
                        continue

                    # Find the index of parent_sku in the prodf DataFrame
                    try:
                        start_index = prodf.loc[prodf['SKU'] == parent_sku].index[0]  # Get the first matching index
                    except IndexError:
                        print(f"Parent SKU {parent_sku} not found in the DataFrame.")
                        start_index = None
                    
                    if start_index is not None:
                        # Get Children SKUs
                        try:
                            children_skus = get_children_skus(parent_sku, prodf, start_index)
                            print(f"\n Child SKU {children_skus} found at index")
                            with logging_lock:
                                logging.info(f"\n Successfully obtained Children_SKUs {children_skus} at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
                        except Exception as e:
                            with logging_lock:
                                logging.error(f"\n Failed to obtain Children_SKUs at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}: {e}")
                            print(f"\n Failed to obtain Children_SKUs: {e}")
                            continue
                        
                    # Load the thread library from file
                    threaddf = load_and_prepare_csv(threaddf_file_path, "Thread Library")
                    with logging_lock:
                        logging.info(f"\n Thread library opened {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
                    print(f"\n Thread library opened at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")        
                    
                    # Set Threading Logic
                    try:
                        threaddf = threading_logic(productSKU, parent_sku, threaddf, client)
                        thread_id = threaddf[1]
                        with logging_lock:
                            logging.info(f"\n Thread ID obtained for SKU {productSKU} at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
                        print(f"\n Thread ID obtained for SKU {productSKU} at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
                    except Exception as threading_error:
                        with logging_lock:
                            logging.error(f"\n Failed to handle threading logic for SKU {productSKU}: {str(threading_error)}")
                        print(f"\n Failed to handle threading logic for SKU {productSKU}: {str(threading_error)}")
                        raise
                    
                    # Debug prints
                    print(f"Thread ID: {threaddf[1]}")
                    print(f"{threaddf}")
                    
                    # Generate a product name with specific formatting requirements, using the getChatCompletions function
                    
                    # Handle NaN values
                    if pd.isna(productName):
                        productName = ''
                        
                    try:
                        # Set xxx variable to productName
                        xxx = productName
                        logging.info(f"Current Product Name: {productName}")
                        
                        # The coordinating row in the prodf DataFrame being accessed
                        # Extra Parent Product Name
                        DFObject = 'Name'
                        parentProductName = extractedparentinfo(parent_sku, DFObject, prodf)
                        
                        # Extract Parent ProductLDescription
                        DFObject = 'Description'
                        parentProductLDescription = extractedparentinfo(parent_sku, DFObject, prodf)
                        parentProductLDescription = sanitize_description(parentProductLDescription)
                        
                        # Log extractions 
                        logging.info(f"\n Setting parent dataframe information: {parentProductName}")
                        print(f"\n Setting parent dataframe information: {parentProductName}, {parentProductLDescription}")
                        
                        # Parent Product Name Request
                        responseParentProduct = (
                            "Write a unique title aimed at all pet owners but primarily appealing to ferret lovers. Deliberately remove names of other animals unless it's essential to the product description.\n"
                            "The product name must include the specific product variant size or sizes available; S, M, and L denoting small, medium, and large, and color or colors the item is in. It also may include information regarding whether or not it is a single item or a set." 
                            "\n Return only the product name, the size, the color, the theme/style (if any), and if it is a part of a set.\n"
                            f"Product Name: {productName}, \n Product Description: {productLDescription}."
                        )
                        
                        # Child Product Name Request
                        responseChildProduct = (
                            f"This product is a variation of the parent product. Write a product name modeled after the parent product listing name but with specification for the product variation. Accurately match details from the productName, {productSKU} and product description against the Parent Product Listing Description to ensure accuracy for the variant. Title should be aimed at all pet owners but primarily appealing to ferret lovers. Deliberately remove names of other animals unless it's essential to the product description. \n"
                            "The product name must include the product variant size or sizes available; S, M, and L denoting small, medium, and large, and color or colors the item is in.\n"
                            "It also may include information regarding whether or not it is a single item or a set, return only the product name, the size, the color, and if it is a part of a set.\n"
                            " If there is no existing Parent product listing name then you may you invent a new product name based on the other available information. \n"
                            f"Parent Product Listing Name: {parentProductName}, Current Product Name: {productName}, \n Current parent product listing: {parentProductLDescription}, Current product listing: {productLDescription}. \n"
                        )
                        logging.info("\n Setting Parent and Child Product responses.")
                        
                        resultProductName = getChatCompletions(
                            openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, 
                            responseChildProduct, thread_id, m_assistant_id, client
                        )
                        # resultProductName = sanitize_description(resultProductName)
                        
                        updatedataframe(prodf, count, 'Name', resultProductName, productlisting_file_path)
                        
                        print(f"Successfully generated {resultProductName} for {productSKU} at {currentDateTime}")
                        with logging_lock:                            
                            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            logging.info(f"Successfully generated {resultProductName} for {productSKU} at {currentDateTime}")
                    
                    except Exception as e:
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        with logging_lock:
                            logging.error(f"\n Failed to generate outcome to replace productName for {productSKU} at {currentDateTime}: {str(e)}")
                        print(f"\n Failed to generate outcome to replace productName for {productSKU} at {currentDateTime}: {str(e)}")
                    
                    # Generate a productSDescription with specific formatting requirements, using the getChatCompletions function
                    
                    # Handle NaN values
                    if pd.isna(productSDescription):
                        productSDescription = ''                    
                    
                    try:
                        # Set xxx variable to productSDescription
                        xxx = productSDescription
                        logging.info(f"\n Current productSDescription: {xxx}")
                        print(f"\n Current productSDescription: {xxx}")
                     
                        # The coordinating row in the prodf DataFrame being accessed
                        # Extra Parent productSDescription 
                        DFObject = 'Short description'
                        parentProductSDescription = extractedparentinfo(parent_sku, DFObject, prodf)
                            
                        # Log extractions 
                        logging.info(f"\n Setting parentProductSDescription dataframe information: {parentProductSDescription}")
                        print(f"\n Setting parentProductSDescription dataframe information: {parentProductSDescription}")
                    
                        # Parent Product Request
                        responseParentProduct = (
                            f"Write a short marketing spiel for the product aimed at all pet owners but primarily appealing to ferret lovers.\n"
                            "This should only be 2 sentences long. The response should include only the 2 sentences requested.\n"
                        )
                    
                        # Child Product Request
                        responseChildProduct = (
                            f"Remembering that this product is a variation of the parent product, write a short marketing spiel specific to the product SKU ({productSKU}) and existing name ({resultProductName}). The description should be modeled after the existing variable short description. Existing variable short description: {parentProductSDescription}. \n "
                            "Where no variable short description is supplied, or the variable short description reads 'nan', write a short marketing spiel for the product aimed at all pet owners but primarily appealing to ferret lovers and that is specific to the variant. Only write a product short description modeled after the parent product listing name where one exists, and always be specific to the current product, not to the variable (or parent product). Accurately match the {productSKU} against the Parent Product Listing Description for greater specificity. Short description should be aimed at all pet owners but primarily appealing to ferret lovers. Deliberately remove names of other animals unless it's essential to the product description.\n "
                            "This should only be 2 sentences long. The response should include only the 2 sentences requested.\n "
                        )
                    
                        logging.info("\n Setting Parent and Child Product responses.")
                    
                        resultProductSDescription = getChatCompletions(
                            openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, 
                            responseChildProduct, thread_id, m_assistant_id, client
                        )
                        # resultProductSDescription = sanitize_description(resultProductSDescription)
                        
                        updatedataframe(prodf, count, 'Short description', resultProductSDescription, productlisting_file_path)

                        with logging_lock:
                            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            logging.info(f"\n Successfully generated {resultProductSDescription} for {productSKU} at {currentDateTime}")
                        print(f"\n Successfully generated {resultProductSDescription} for {productSKU} at {currentDateTime}")
                            
                    except Exception as e:
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        with logging_lock:
                            logging.error(f"\n Failed to generate product short description for {productSKU} at {currentDateTime}: {str(e)}")
                        print(f"\n Failed to generate product short description for {productSKU} at {currentDateTime}: {str(e)}")
                    
                    # Handle NaN values for productCategories
                    if pd.isna(productCategories):
                        productCategories = ''  
                    
                    try:
                        logging.info("Generating product categories...")
                    
                        # 1. Check if productCategories is already assigned and not empty
                        if productCategories and productCategories.strip():
                            resultProductCategories = productCategories
                            logging.info(f"\n Product categories already exist for {productSKU}: {productCategories}")
                            print(f"\n Product categories already exist for {productSKU}: {productCategories}")
                        
                        else:
                            # 2. If no categories exist, attempt to find a matching category from the category_map
                            category_key = None
                            for key in category_map:
                                if key in productName.lower():  # Assuming productName contains the name of the product
                                    category_key = key
                                    break
                    
                            if category_key:
                                # If a matching category is found in the category_map
                                resultProductCategories = " > ".join(category_map[category_key])
                                resultProductCategories = sanitize_description(resultProductCategories)
                                
                                currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                logging.info(f"\n Matched product '{productName}' with category '{resultProductCategories}' using key '{category_key}' at {currentDateTime}")
                                print(f"\n Matched product '{productName}' with category '{resultProductCategories}' using key '{category_key}' at {currentDateTime}")
                    
                            else:
                                # 3. If no matching category is found in the map, generate categories using getChatCompletions
                                # Set xxx variable to productCategories
                                xxx = productCategories or "Uncategorized"
                                logging.info(f"\n Current productCategories: {xxx}")
                                print(f"\n Current productCategories: {xxx}")
                                
                                # Extract parent product information for additional context in the API request
                                DFObject = 'Categories'
                                parentProductCategories = extractedparentinfo(parent_sku, DFObject, prodf)
                                
                                DFObject = 'Length (cm)'
                                parentProductLength = extractedparentinfo(parent_sku, DFObject, prodf)            
                                
                                DFObject = 'Width (cm)'
                                parentProductWidth = extractedparentinfo(parent_sku, DFObject, prodf)              
                                
                                DFObject = 'Height (cm)'
                                parentProductHeight = extractedparentinfo(parent_sku, DFObject, prodf)
                                
                                DFObject = 'Weight (kg)'
                                parentProductWeight = extractedparentinfo(parent_sku, DFObject, prodf)
                                
                                # Log extractions 
                                logging.info(f"\n Setting parent dataframe information: PARENT PRODUCT CATEGORIES {parentProductCategories}, PARENT PRODUCT LENGTH {parentProductLength}, PARENT PRODUCT WIDTH {parentProductWidth}, PARENT PRODUCT HEIGHT {parentProductHeight}, PARENT PRODUCT WEIGHT {parentProductWeight}")
                                print(f"\n Setting parent dataframe information: PARENT PRODUCT CATEGORIES {parentProductCategories}, PARENT PRODUCT LENGTH {parentProductLength}, PARENT PRODUCT WIDTH {parentProductWidth}, PARENT PRODUCT HEIGHT {parentProductHeight}, PARENT PRODUCT WEIGHT {parentProductWeight}")
                            
                                # Parent Product Request
                                responseParentProduct = (
                                    "Use any and all relevant information, including the Category Map below, to assess the appropriate product Categories for {productSKU} {resultProductName}. "
                                    "All dookery.com products must have a For Ferrets or For Humans tag, as well as a primary Category. If the primary Category is a sub-category, then all Categories from superior Categories must also be listed. "
                                    "For example, if product is a Leash, Categories must include 'Play & Train, Training Aids & Other Tools, Leashes, For Ferrets', or if product is Wall Decal, Categories should be 'Lifestyle, Homeware, Wall Decals, For Humans'.\n"
                                    f"Output must then be formatted according to the Category Map. Return only in this format. No product description or long form text should be output.\n"
                                    f"Category Map: {category_map}.\n"
                                    f"Additional Context from the product file: Product Length: {productLength}. Product Width: {productWidth}. Product Height: {productHeight}. Product Weight: {productWeight}. Existing productCategories: {productCategories}. \n"
                                )
                            
                                # Child Product Request
                                responseChildProduct = (
                                    f"Remembering that this product is a variation of the parent product, use any and all relevant information, including the Category Map below, to assess the appropriate product Categories for {productSKU} {resultProductName}. "
                                    "Responses must be modeled after variable Categories offered if there are any. Variable Categories: {parentProductCategories}.\n"
                                    "All dookery.com products must have a For Ferrets or For Humans tag, as well as a primary Category. If the primary Category is a sub-category, then all Categories from superior Categories must also be listed. "
                                    "For example, if product is a Leash, Categories must include 'Play & Train, Training Aids & Other Tools, Leashes, For Ferrets', or if product is Wall Decal, Categories should be 'Lifestyle, Homeware, Wall Decals, For Humans'.\n"
                                    f"Output must then be formatted according to the Category Map and returned as a string. Return only in this format. No product description or long form text should be output.\n"
                                    f"Category Map: {category_map}.\n"
                                    f"Additional context from the {productSKU} variant product file: Product Length: {productLength}. Product Width: {productWidth}. Product Height: {productHeight}. Product Weight: {productWeight}. Existing productCategories: {productCategories}.\n"
                                    f"Additional context from the {parent_sku} parent product file (remember the output must be specific to the variant, but should reinforce information offered by the variable where relevant): Variable Product Length: {parentProductLength}. Variable Product Width: {parentProductWidth}. Variable Product Height: {parentProductHeight}. Variable Product Weight: {parentProductWeight}.\n"
                                )
                            
                                logging.info("\n Setting Parent and Child Product responses.")
                            
                                resultProductCategories = getChatCompletions(
                                    openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, 
                                    responseChildProduct, thread_id, m_assistant_id, client
                                )
                                # resultProductCategories = sanitize_description(resultProductCategories)

                                with logging_lock:
                                    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                    logging.info(f"\n Successfully generated Categories: {resultProductCategories} for {productSKU} at {currentDateTime}")
                                print(f"\n Successfully generated Categories: {resultProductCategories} for {productSKU} at {currentDateTime}")
                                    
                    except Exception as e:
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        with logging_lock:
                            logging.error(f"\n Failed to generate {xxx} for {productSKU} at {currentDateTime}: {str(e)}")
                        print(f"\n Failed to generate {xxx} for {productSKU} at {currentDateTime}: {str(e)}")
                    
                    updatedataframe(prodf, count, 'Categories', resultProductCategories, productlisting_file_path)
                    
                    # Generate Product Tags with specific formatting requirements, using the getChatCompletions function
                    try:
                        logging.info("Generating product Tags...")
                    
                        # 1. Check if productTags is already assigned and not empty
                        if productTags and productTags.strip():
                            resultProductTags = productTags
                            logging.info(f"\n Product Tags already exist for {productSKU}: {productTags}")
                            print(f"\n Product Tags already exist for {productSKU}: {productTags}")
                        
                        else:
                            # 2. If no Tags exist, attempt to find a matching tag from the tag_map
                            tag_key = None
                            for key in tag_map:
                                if key in productName.lower():
                                    tag_key = key
                                    break
                    
                            if tag_key:
                                # If a matching tag is found in the tag_map
                                resultProductTags = " > ".join(tag_map[tag_key])
                                resultProductTags = sanitize_description(resultProductTags)
                                
                                currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                logging.info(f"\n Matched product '{productName}' with existing tags: '{resultProductTags}', using key '{tag_key}' at {currentDateTime}")
                                print(f"\n Matched product '{productName}' with existing tags: '{resultProductTags}', using key '{tag_key}' at {currentDateTime}")
                    
                            else:
                                # 3. If no matching tag is found in the map, generate Tags using getChatCompletions
                                # Set xxx variable to productTags
                                xxx = productTags or "Uncategorized"
                                logging.info(f"\n Current productTags: {xxx}")
                                print(f"\n Current productTags: {xxx}")
                                
                                # Extract parent product information for additional context in the API request
                                DFObject = 'Tags'
                                parentProductTags = extractedparentinfo(parent_sku, DFObject, prodf)
                                
                                # Log extractions 
                                logging.info(f"\n Setting parent dataframe information: PARENT PRODUCT TAGS {parentProductTags}")
                                print(f"\n Setting parent dataframe information: PARENT PRODUCT TAGS {parentProductTags}")
                                
                                # Parent Product Request
                                responseParentProduct = (
                                    "Use any and all relevant information, including the Tag Map below, to assess the appropriate product Tags for {productSKU} {resultProductName}. "
                                    "All dookery.com products must have a For Ferrets or For Humans tag, as well as all additional relevant tags.There is no tag hierarchy or limit on number of tags a product can have, however if a tag matches a category from the Category_Map then the tag output must include (at a minimum) all listed categories as comma separated tags"
                                    "e.g. 'leash': 'For Ferrets', 'Play & Train', 'Training Aids & Others Tools', 'Leashes'. All tags should be output as a comma separated string."
                                    f"\n {tag_map}"
                                )
                            
                                # Child Product Request
                                responseChildProduct = (
                                    f"Remembering that this product is a variation of the parent product, use any and all relevant information, including the Tag Map below, and existing information about the parent products tags and categories, to assess the appropriate product Tags for {productSKU} {resultProductName}. "
                                    f"Responses must include variable Tags offered if they are relevant to the current product. Parent/Variable Tags: {parentProductTags}.\n"
                                    "All dookery.com products must have a For Ferrets or For Humans tag, as well as all additional relevant tags.There is no tag hierarchy or limit on number of tags a product can have, however if a tag matches a category from the Category_Map then the tag output must include (at a minimum) all listed categories as comma separated tags"
                                    "e.g. 'leash': 'For Ferrets', 'Play & Train', 'Training Aids & Others Tools', 'Leashes'. All tags should be output as a comma separated string."
                                    f"\n {tag_map}"
                                )
                            
                                logging.info("\n Setting Parent and Child Product responses.")
                            
                                resultProductTags = getChatCompletions(
                                    openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, 
                                    responseChildProduct, thread_id, m_assistant_id, client
                                )
                                # resultProductTags = sanitize_description(resultProductTags)
                    
                                with logging_lock:
                                    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                    logging.info(f"\n Successfully generated Tags: {resultProductTags} for {productSKU} at {currentDateTime}")
                                print(f"\n Successfully generated Tags: {resultProductTags} for {productSKU} at {currentDateTime}")
                                    
                    except Exception as e:
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        with logging_lock:
                            logging.error(f"\n Failed to generate {xxx} for {productSKU} at {currentDateTime}: {str(e)}")
                        print(f"\n Failed to generate {xxx} for {productSKU} at {currentDateTime}: {str(e)}")
                    
                    updatedataframe(prodf, count, 'Tags', resultProductTags, productlisting_file_path)                    
                    
                    # Generate Product Attributes with specific formatting requirements, using the getChatCompletions function
                    try:
                        logging.info("Generating Attributes...")
                        print("Generating Attributes...")
                    
                        # Gather existing data from the product fields
                        productAttributes = {
                            "AttributeOneName": productAttributeOneName,
                            "AttributeOneDesc": productAttributeOneDesc,
                            "AttributeTwoName": productAttributeTwoName,
                            "AttributeTwoDesc": productAttributeTwoDesc,
                            "AttributeThreeName": productAttributeThreeName,
                            "AttributeThreeDesc": productAttributeThreeDesc,
                        }
                        
                        # Handle None or empty values in productAttributes
                        for key, value in productAttributes.items():
                            if pd.isna(value) or value == '':
                                productAttributes[key] = "N/A"                        
                        
                        # Set xxx variable to productAttributes
                        xxx = productAttributes
                        logging.info(f"Current productAttributes: {xxx}")
                        print(f"Current productAttributes: {xxx}")
                        
                        # Extract parent product information for additional context in the API request
                        def get_attribute_or_unknown(sku, column_name):
                            value = extractedparentinfo(sku, column_name, prodf)
                            if pd.isna(value) or value == '':
                                return "Unknown"
                            return value                        

                
                        parentAttributeOneName = get_attribute_or_unknown(parent_sku, 'Attribute 1 name')
                        parentAttributeOneDesc = get_attribute_or_unknown(parent_sku, 'Attribute 1 value(s)')
                        parentAttributeTwoName = get_attribute_or_unknown(parent_sku, 'Attribute 2 name')
                        parentAttributeTwoDesc = get_attribute_or_unknown(parent_sku, 'Attribute 2 value(s)')
                        parentAttributeThreeName = get_attribute_or_unknown(parent_sku, 'Attribute 3 name')
                        parentAttributeThreeDesc = get_attribute_or_unknown(parent_sku, 'Attribute 3 value(s)')
                        
                        # Log extractions
                        logging.info(
                            f"Setting parent dataframe information: PARENT PRODUCT ATTRIBUTES: "
                            f"{parentAttributeOneName}, {parentAttributeOneDesc}, "
                            f"{parentAttributeTwoName}, {parentAttributeTwoDesc}, "
                            f"{parentAttributeThreeName}, {parentAttributeThreeDesc}"
                        )
                        print(
                            f"Setting parent dataframe information: PARENT PRODUCT ATTRIBUTES: "
                            f"{parentAttributeOneName}, {parentAttributeOneDesc}, "
                            f"{parentAttributeTwoName}, {parentAttributeTwoDesc}, "
                            f"{parentAttributeThreeName}, {parentAttributeThreeDesc}"
                        )
                        
                        # Parent Product Request
                        responseParentProduct = (
                            "Use any and all relevant information to assess the 3 most relevant and useful product attributes "
                            "(Name and Description) from the available attributes shown in the attributes_map, existing information, "
                            "and your own best assessment of the product. You are to choose the 3 best attributes available to represent "
                            "the item. You will be given any existing information and must strongly consider it for inclusion in the "
                            "output you create. The output should be a JSON object with the keys: AttributeOneName, AttributeOneDesc, "
                            "AttributeTwoName, AttributeTwoDesc, AttributeThreeName, AttributeThreeDesc."
                            "\nYour response should be only the JSON object, and no additional text."
                            "\nExample JSON format:"
                            "{\n"
                            "  \"AttributeOneName\": \"Color\",\n"
                            "  \"AttributeOneDesc\": \"Blue\",\n"
                            "  \"AttributeTwoName\": \"Size\",\n"
                            "  \"AttributeTwoDesc\": \"Medium\",\n"
                            "  \"AttributeThreeName\": \"Material\",\n"
                            "  \"AttributeThreeDesc\": \"Cotton\"\n"
                            "}"
                            f"\nExisting product data: {productAttributes}"
                            f"\nExisting parent product data: {{'AttributeOneName': '{parentAttributeOneName}', 'AttributeOneDesc': '{parentAttributeOneDesc}', "
                            f"'AttributeTwoName': '{parentAttributeTwoName}', 'AttributeTwoDesc': '{parentAttributeTwoDesc}', "
                            f"'AttributeThreeName': '{parentAttributeThreeName}', 'AttributeThreeDesc': '{parentAttributeThreeDesc}'}}."
                            f"\nAttributes Map: {attributes_map}"
                        )                        
                        
                        # Child Product Request
                        responseChildProduct = (
                            "Remembering that this product is a variation of the parent product, use any and all relevant information to assess the 3 most relevant and useful product attributes "
                            "(Name and Description) from the available attributes shown in the attributes_map, existing information, "
                            "and your own best assessment of the product. You are to choose the 3 best attributes available to represent "
                            "the item. You will be given any existing information and must strongly consider it for inclusion in the "
                            "output you create. The output should be a JSON object with the keys: AttributeOneName, AttributeOneDesc, "
                            "AttributeTwoName, AttributeTwoDesc, AttributeThreeName, AttributeThreeDesc."
                            "\nYour response should be only the JSON object, and no additional text."
                            "\nExample JSON format:"
                            "{\n"
                            "  \"AttributeOneName\": \"Color\",\n"
                            "  \"AttributeOneDesc\": \"Blue\",\n"
                            "  \"AttributeTwoName\": \"Size\",\n"
                            "  \"AttributeTwoDesc\": \"Medium\",\n"
                            "  \"AttributeThreeName\": \"Material\",\n"
                            "  \"AttributeThreeDesc\": \"Cotton\"\n"
                            "}"
                            f"\nExisting product data: {productAttributes}"
                            f"\nExisting parent product data: {{'AttributeOneName': '{parentAttributeOneName}', 'AttributeOneDesc': '{parentAttributeOneDesc}', "
                            f"'AttributeTwoName': '{parentAttributeTwoName}', 'AttributeTwoDesc': '{parentAttributeTwoDesc}', "
                            f"'AttributeThreeName': '{parentAttributeThreeName}', 'AttributeThreeDesc': '{parentAttributeThreeDesc}'}}."
                            f"\nAttributes Map: {attributes_map}"
                        )                        
                                           
                        logging.info("Setting Parent and Child Product responses.")
                        print("Setting Parent and Child Product responses.")
                    
                        # Call getChatCompletions function to get AI-generated attributes
                        try:
                            resultProductAttributes = getChatCompletions(
                                openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
                            )
                            if not resultProductAttributes:
                                raise ValueError("AI response is empty")
                        except Exception as e:
                            logging.error(f"Error during AI call: {str(e)}")
                            raise

                        # Log the AI response
                        logging.info(f"AI Response for Attributes: {resultProductAttributes}")
                        print(f"AI Response for Attributes: {resultProductAttributes}")
                
                        # Parse the AI response (extract JSON)
                        try:
                            # Use regular expression to find the JSON object in the response
                            import re
                            json_pattern = re.compile(r'\{.*\}', re.DOTALL)
                            match = json_pattern.search(resultProductAttributes)
                            if match:
                                json_str = match.group(0)
                                resultAttributes = json.loads(json_str)
                                logging.info("Successfully extracted and parsed AI response into JSON.")
                                print("Successfully extracted and parsed AI response into JSON.")
                            else:
                                logging.error("No JSON object found in AI response.")
                                print("No JSON object found in AI response.")
                                raise ValueError("No JSON object found in AI response.")
                        except json.JSONDecodeError as e:
                            logging.error(f"Failed to parse AI response as JSON: {e}")
                            print(f"Failed to parse AI response as JSON: {e}")
                            raise
                
                        # Assign the AI-generated attributes to the relevant fields
                        productAttributeOneName = resultAttributes.get("AttributeOneName", productAttributeOneName)
                        productAttributeOneDesc = resultAttributes.get("AttributeOneDesc", productAttributeOneDesc)
                        productAttributeTwoName = resultAttributes.get("AttributeTwoName", productAttributeTwoName)
                        productAttributeTwoDesc = resultAttributes.get("AttributeTwoDesc", productAttributeTwoDesc)
                        productAttributeThreeName = resultAttributes.get("AttributeThreeName", productAttributeThreeName)
                        productAttributeThreeDesc = resultAttributes.get("AttributeThreeDesc", productAttributeThreeDesc)

                        # Update the DataFrame with the new attributes
                        with prodf_lock:
                            prodf.loc[count, 'Attribute 1 name'] = productAttributeOneName
                            prodf.loc[count, 'Attribute 1 value(s)'] = productAttributeOneDesc
                            prodf.loc[count, 'Attribute 2 name'] = productAttributeTwoName
                            prodf.loc[count, 'Attribute 2 value(s)'] = productAttributeTwoDesc
                            prodf.loc[count, 'Attribute 3 name'] = productAttributeThreeName
                            prodf.loc[count, 'Attribute 3 value(s)'] = productAttributeThreeDesc
                
                        # Save the updated DataFrame to CSV
                        with prodf_lock:
                            prodf.to_csv(productlisting_file_path, index=False, encoding='utf-8')
                        logging.info(f"DataFrame saved to {productlisting_file_path} after updating attributes.")
                        print(f"DataFrame saved to {productlisting_file_path} after updating attributes.")
                
                        # Log the success of attribute generation
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        logging.info(f"Successfully generated attributes for {productName} at {currentDateTime}")
                        print(f"Successfully generated attributes for {productName} at {currentDateTime}")
                
                        # Log the recommended updates to the attributes_map
                        attribute_names = [
                            (productAttributeOneName, productAttributeOneDesc),
                            (productAttributeTwoName, productAttributeTwoDesc),
                            (productAttributeThreeName, productAttributeThreeDesc)
                        ]
                
                        for attr_name, attr_value in attribute_names:
                            if attr_name and attr_value:
                                if attr_name not in attributes_map:
                                    attributes_map[attr_name] = [attr_value]
                                    logging.info(f"Recommended Attribute_Map Update: Added new attribute '{attr_name}' with value '{attr_value}'")
                                    print(f"Recommended Attribute_Map Update: Added new attribute '{attr_name}' with value '{attr_value}'")
                                elif attr_value not in attributes_map[attr_name]:
                                    attributes_map[attr_name].append(attr_value)
                                    logging.info(f"Recommended Attribute_Map Update: Added new value '{attr_value}' to attribute '{attr_name}'")
                                    print(f"Recommended Attribute_Map Update: Added new value '{attr_value}' to attribute '{attr_name}'")
                
                    except Exception as e:
                        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        logging.error(f"Failed to generate attributes for {productName} at {currentDateTime}: {str(e)}")
                        print(f"Failed to generate attributes for {productName} at {currentDateTime}: {str(e)}")
                    

                
            else:
                currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                with logging_lock:
                    logging.warning(f"Product processing skipped {count + 1} due to count out of range at {currentDateTime}")
                print(f"Product entries exceeded array limit.")
                continue
                
        except Exception as e:
            with logging_lock:
                logging.error(f"Error processing product {count + 1}: {e}")
            print(f"Error processing product {count + 1}: {e}") 


    print("Product processing completed!")

# Entry point of the script
if __name__ == '__main__':
    print("Script is accessing Main logic...")
    main(
        skudf_file_path=skudf_file_path,
        skujson_file_path=skujson_file_path,
        productlisting_file_path=productlisting_file_path,
        threaddf_file_path=threaddf_file_path,
        productlistingjson_file_path=productlistingjson_file_path,
        openai_api_key=openai_api_key,
        organization_id=organization_id,
        project_id=project_id,
        base_url=base_url,
        marketing_personality=dookery.marketing_personality,
        category_map=dookery.category_map,
        tag_map=dookery.tag_map,
        attributes_map=dookery.attributes_map,
        # complementary_map=dookery.complementary_map
        logging=logging,
        logging_lock=logging_lock,
    )
    logging.warning("\n Warming Up: Let's go!!!")
    print("\n Warming Up: Let's go!!!")



#################### SCRAP CODE TO CLEAN ############################

import openai
import pandas as pd
import csv
import logging
from datetime import datetime
import os

# Define marketing personality
marketingPersonality = (
    "You are a Marketing Genius creating product listings for The Dookery, a website dedicated to providing high-quality ferret-related products. "
    "Your focus is on emphasizing the usefulness and comfort of these products for ferrets and ferret lovers. Your tone is honest, authentic, super friendly, and trustworthy. "
    "You always apply the best standards for marketing to all output you create and use all of the most modern methods in your practices. "
    "You always emphasize the luxuriousness and quality of product sets. You spell out the obvious to avoid assumptions of buyer knowledge, and use emojis to enhance your text readability."
    "Product Categories include the following: Adventure (For Ferrets) includes sub-categories such as Adventure Gift Baskets (For Ferrets), Adventure Learn (For Humans), Adventure Subscription (For Ferrets), "
    "Carry Bags & Cages (For Ferrets), Digital Devices (For Ferrets) which further includes GPS Trackers (For Ferrets), Travel Bedding (For Ferrets), and Travel Food & Water Bowls (For Ferrets). "
    "Essentials (For Ferrets) encompasses Bedding & Blankets (For Ferrets), Cages (For Ferrets), Essentials Gift Baskets (For Ferrets), Essentials Learn (For Humans), Essentials Subscription (For Ferrets), "
    "Food (For Ferrets), Food & Water Bowls (For Ferrets), Grooming Tools (For Ferrets), and Litter Trays (For Ferrets). "
    "Lifestyle (For Ferrets) (For Humans) includes Access Steps (For Ferrets), Apparel & Accessories (For Humans) (For Ferrets) with sub-categories like Bracelets (For Humans), Costumes (For Humans) which includes Ferret Costumes (For Ferrets) and Human Costumes (For Humans), "
    "Earrings (For Humans), Hairpieces (For Humans), Hoodies (For Humans), Necklaces (For Humans), Onesies (For Humans), Rings (For Humans), Socks (For Humans), and Tops (For Humans), "
    "Digital Devices (For Ferrets) with sub-categories such as Food & Water Bowls (For Ferrets), Grooming Tools (For Ferrets), Litter Trays (For Ferrets), and Pet Cameras (For Ferrets), "
    "Homeware (For Humans) which includes Art Prints (For Humans), Calendars (For Humans), Cushions & Bedding (For Humans), Custom Ferret Portrait (For Humans), Keychains (For Humans), Phone Cases (For Humans), "
    "Plates & Mugs (For Humans), Stationary (For Humans) which includes Diaries & Notebooks (For Humans), Pens (For Humans), and Stickers (For Humans), Wall Decals (For Humans), "
    "Lifestyle Gift Baskets (For Humans), Lifestyle Learn (For Humans), and Lifestyle Subscription (For Humans). "
    "Play & Train (For Ferrets) comprises Ferret Training Guides (For Humans), Play & Train Gift Baskets (For Ferrets), Play & Train Learn (For Humans), Play & Train Subscription (For Ferrets) (For Humans), "
    "Play Pens (For Ferrets), Toys (For Ferrets), Training Aids & Other Tools (For Ferrets) which includes Books & Others Resources (For Humans), Clickers (For Ferrets), Collars (For Ferrets), Harnesses (For Ferrets), Leashes (For Ferrets), and Treats (For Ferrets), "
    "and Workshops & Others Courses (For Humans). Uncategorized is also available for products that do not fit into the other categories."
    "Unique Selling Points: The Dookery is a centralized platform catering to the specific needs of ferret owners and lovers, it offers a range of ferret-themed goods and necessities, "
    "ensuring a comprehensive and trusted marketplace for quality and safe products, and it strives to be more than a marketplace by providing educational resources, vet contacts, classes, and grants, converting it into a community hub for learning, interaction, and collaboration towards better ferret care."
    "Target Audience: Individuals who own or are interested in owning ferrets, typically aged between 25 and 45, with an annual income of $50,000-$100,000. "
    "These customers are willing to spend on high-quality products and services, averaging $100-$200 monthly on supplies and $500-$1000 annually on veterinary care, "
    "and/or They are active in the pet community and on social media platforms like Facebook and Instagram, sharing their passion for ferrets."
    "Tone and Brand Voice: Friendly, authentic, trustworthy, sweet, kind, and hopeful, Emphasize luxuriousness and quality in product sets, Use emojis to enhance text readability."
    "Scientific Accuracy and Real-World Usage: follow academic standards for scientific accuracy, citing academic knowledge or offering it with caution, Describe real-world usage scenarios, "
    "considering ferret-specific safety standards and needs, and any potential impacts on other pets or children in the household. Your advice is scientifically accurate, describes real-world usage scenarios, "
    "considers ferret-specific safety standards and needs, and considers any potential impacts on any pet or child in the household from product usage."
    "Key Messages: We're here to help and we want your feedback. This is about us serving you to the best of our abilities, so tell us how to do that. Be kind to yourself and your ferrets. You all deserve the best life."
)
# Define the category map
category_map = {
    "leash": ["For Ferrets", "Play & Train > Training Aids & Other Tools > Leashes"],
    "wall decal": ["Lifestyle > Homeware > Wall Decals", "For Humans"],
    "bedding": ["Essentials > Bedding & Blankets", "For Ferrets"],
    "food bowl": ["Essentials > Food & Water Bowls", "For Ferrets"],
    "travel bowl": ["Adventure > Travel Food & Water Bowls", "For Ferrets"],
    "harness": ["For Ferrets", "Play & Train > Training Aids & Other Tools > Harnesses"],
    "collar": ["For Ferrets", "Play & Train > Training Aids & Other Tools > Collars"],
    "adventure gift basket": ["Adventure > Adventure Gift Baskets", "For Ferrets"],
    "adventure learn": ["Adventure > Adventure Learn", "For Humans"],
    "adventure subscription": ["Adventure > Adventure Subscription", "For Ferrets"],
    "carry bag": ["Adventure > Carry Bags & Cages", "For Ferrets"],
    "cage": ["Essentials > Cages", "For Ferrets"],
    "digital device": ["Adventure > Digital Devices", "For Ferrets"],
    "gps tracker": ["Adventure > Digital Devices > GPS Trackers", "For Ferrets"],
    "travel bedding": ["Adventure > Travel Bedding", "For Ferrets"],
    "food": ["Essentials > Food", "For Ferrets"],
    "grooming tool": ["Essentials > Grooming Tools", "For Ferrets"],
    "litter tray": ["Essentials > Litter Trays", "For Ferrets"],
    "access step": ["Lifestyle > Access Steps", "For Ferrets"],
    "bracelet": ["Lifestyle > Apparel & Accessories > Bracelets", "For Humans"],
    "costume": ["Lifestyle > Apparel & Accessories > Costumes", "For Humans"],
    "ferret costume": ["Lifestyle > Apparel & Accessories > Ferret Costumes", "For Ferrets"],
    "human costume": ["Lifestyle > Apparel & Accessories > Human Costumes", "For Humans"],
    "earring": ["Lifestyle > Apparel & Accessories > Earrings", "For Humans"],
    "hairpiece": ["Lifestyle > Apparel & Accessories > Hairpieces", "For Humans"],
    "hoodie": ["Lifestyle > Apparel & Accessories > Hoodies", "For Humans"],
    "necklace": ["Lifestyle > Apparel & Accessories > Necklaces", "For Humans"],
    "onesie": ["Lifestyle > Apparel & Accessories > Onesies", "For Humans"],
    "ring": ["Lifestyle > Apparel & Accessories > Rings", "For Humans"],
    "sock": ["Lifestyle > Apparel & Accessories > Socks", "For Humans"],
    "top": ["Lifestyle > Apparel & Accessories > Tops", "For Humans"],
    "pet camera": ["Lifestyle > Digital Devices > Pet Cameras", "For Ferrets"],
    "art print": ["Lifestyle > Homeware > Art Prints", "For Humans"],
    "calendar": ["Lifestyle > Homeware > Calendars", "For Humans"],
    "cushion": ["Lifestyle > Homeware > Cushions & Bedding", "For Humans"],
    "custom ferret portrait": ["Lifestyle > Homeware > Custom Ferret Portrait", "For Humans"],
    "keychain": ["Lifestyle > Homeware > Keychains", "For Humans"],
    "phone case": ["Lifestyle > Homeware > Phone Cases", "For Humans"],
    "plate": ["Lifestyle > Homeware > Plates & Mugs", "For Humans"],
    "stationary": ["Lifestyle > Homeware > Stationary", "For Humans"],
    "diary": ["Lifestyle > Homeware > Stationary > Diaries & Notebooks", "For Humans"],
    "pen": ["Lifestyle > Homeware > Stationary > Pens", "For Humans"],
    "sticker": ["Lifestyle > Homeware > Stationary > Stickers", "For Humans"],
    "lifestyle gift basket": ["Lifestyle > Lifestyle Gift Baskets", "For Humans"],
    "lifestyle learn": ["Lifestyle > Lifestyle Learn", "For Humans"],
    "lifestyle subscription": ["Lifestyle > Lifestyle Subscription", "For Humans"],
    "ferret training guide": ["Play & Train > Ferret Training Guides", "For Humans"],
    "play & train gift basket": ["Play & Train > Play & Train Gift Baskets", "For Ferrets"],
    "play & train learn": ["Play & Train > Play & Train Learn", "For Humans"],
    "play & train subscription": ["For Ferrets", "For Humans", "Play & Train > Play & Train Subscription"],
    "play pen": ["Play & Train > Play Pens", "For Ferrets"],
    "toy": ["For Ferrets", "Play & Train > Toys"],
    "training aid": ["For Ferrets", "Play & Train > Training Aids & Other Tools"],
    "book": ["Play & Train > Training Aids & Other Tools > Books & Others Resources", "For Humans"],
    "clicker": ["For Ferrets", "Play & Train > Training Aids & Other Tools > Clickers"],
    "treat": ["For Ferrets", "Play & Train > Training Aids & Other Tools > Treats"],
    "workshop": ["Play & Train > Workshops & Others Courses", "For Humans"],
    "course": ["Play & Train > Workshops & Others Courses", "For Humans"],
    "uncategorised": ["Uncategorised"],
}

# Define the Attributes_Map
attributes_map = {
    "artist": ["FerretFatale", "SitcomReality"],
    "childrens-clothing-sizes": [
        "Big Kids US 10, EU 146-152, UK 9-10 years", "Big Kids US 12, EU 158-164, UK 11-12 years",
        "Big Kids US 14, EU 158-164, UK 13-14 years", "Big Kids US 16, EU 170-176, UK 13-14 years",
        "Big Kids US 4, EU 134-140, UK 5-6 years", "Big Kids US 5, EU 134-140, UK 6-7 years",
        "Big Kids US 6, EU 134-140, UK 6-7years", "Big Kids US 7, EU 146-152, UK 7-8 years",
        "Big Kids US 8, EU 146-152, UK 8-9 years", "Infant: US 3-6 months, EU 62-68, UK 3-6 months",
        "Infant: US 6-9 months, EU 74-80, UK 6-9 months", "Infant: US 9-12 months, EU 74-80, UK 9-12 months",
        "Little Kids US 2T, EU 110-116, UK 2-3years", "Little Kids US 3T, EU 110-116, UK 3-4 years",
        "Little Kids US 4T, EU 122-128, UK 4-5 years", "Little Kids US 5T, EU 122-128, UK 4-5years",
        "Newborn: US 0-3 months, EU 50-56, UK 0-3 months", "Toddler: US 12-18 months, EU 86-92, UK 12-18 months",
        "Toddler: US 18-24 months, EU 98-104, UK 18-24 months"
    ],
    "color": [
        "Aqua", "Beige", "Black", "Blue", "Brown", "Burgundy", "Chocolate", "Coral", "Cream",
        "Fuchsia", "Gold", "Gray", "Green", "Ivory", "Khaki", "Lavender", "Light Pink", "Lime",
        "Magenta", "Maroon", "Mint", "Multicolor", "Navy", "Neon", "Olive", "Orange", "Pastel",
        "Peach", "Pink", "Plum", "Purple", "Red", "Royal Blue", "Silver", "Sky Blue", "Tan",
        "Teal", "Turquoise", "Violet", "White", "Yellow"
    ],
    "mens-clothing-sizes": [
        "Extra Extra Large: US 50-52, EU 60-62, UK 50-52", "Extra Large: US 46-48, EU 56-58, UK 46-48",
        "Extra-Small: US 34, EU 44, UK 34", "Large: US 42-44, EU 52-54, UK 42-44",
        "Medium: US 38-40, EU 48-50, UK 38-40", "Small: US 36, EU 46, UK 36"
    ],
    "womens-clothing-sizes": [
        "Extra Extra Large: US 20-22, EU 52-54, UK 24-26", "Extra Large: US 16-18, EU 48-50, UK 20-22",
        "Extra Small: US 0-2, EU 32-34, UK 4-6", "Large: US 12-14, EU 44-46, UK 16-18",
        "Medium: US 8-10, EU 40-42, UK 12-14", "Small: US 4-6, EU 36-38, UK 8-10"
    ]
}

#Define the Complementary_Map
complementary_map = {
    "Adventure": ["Travel Bedding", "Carry Bags & Cages", "GPS Trackers", "Travel Food & Water Bowls"],
    "Adventure Gift Baskets": ["Travel Bedding", "GPS Trackers", "Carry Bags & Cages"],
    "Adventure Learn": ["Ferret Training Guides", "Workshops & Others Courses"],
    "Adventure Subscription": ["Travel Bedding", "GPS Trackers", "Digital Devices"],
    "Carry Bags & Cages": ["Travel Bedding", "GPS Trackers", "Leashes"],
    "Digital Devices": ["Pet Cameras", "GPS Trackers", "Training Aids & Other Tools"],
    "GPS Trackers": ["Carry Bags & Cages", "Leashes", "Harnesses"],
    "Travel Bedding": ["Carry Bags & Cages", "Blankets", "Essentials Subscription"],
    "Travel Food & Water Bowls": ["Carry Bags & Cages", "Treats", "Essentials Subscription"],
    
    "Essentials": ["Bedding & Blankets", "Litter Trays", "Grooming Tools"],
    "Bedding & Blankets": ["Travel Bedding", "Essentials Subscription", "Cushions & Bedding"],
    "Cages": ["Bedding & Blankets", "Litter Trays", "Food & Water Bowls"],
    "Essentials Gift Baskets": ["Bedding & Blankets", "Litter Trays", "Grooming Tools"],
    "Essentials Learn": ["Ferret Training Guides", "Workshops & Others Courses"],
    "Essentials Subscription": ["Bedding & Blankets", "Litter Trays", "Grooming Tools"],
    "Food": ["Food & Water Bowls", "Treats", "Essentials Subscription"],
    "Food & Water Bowls": ["Cages", "Treats", "Training Aids & Other Tools"],
    "Grooming Tools": ["Litter Trays", "Essentials Subscription", "Digital Devices"],
    "Litter Trays": ["Bedding & Blankets", "Essentials Subscription", "Grooming Tools"],
    
    "Lifestyle": ["Homeware", "Apparel & Accessories", "Digital Devices"],
    "Access Steps": ["Cages", "Bedding & Blankets", "Training Aids & Other Tools"],
    "Apparel & Accessories": ["Homeware", "Lifestyle Gift Baskets", "Lifestyle Subscription"],
    "Bracelets": ["Necklaces", "Rings", "Keychains"],
    "Costumes": ["Hoodies", "Onesies", "Ferret Costumes"],
    "Ferret Costumes": ["Human Costumes", "Apparel & Accessories", "Lifestyle Subscription"],
    "Human Costumes": ["Ferret Costumes", "Onesies", "Socks"],
    "Earrings": ["Necklaces", "Bracelets", "Rings"],
    "Hairpieces": ["Hoodies", "Tops", "Socks"],
    "Hoodies": ["Onesies", "Tops", "Human Costumes"],
    "Necklaces": ["Bracelets", "Earrings", "Rings"],
    "Onesies": ["Hoodies", "Socks", "Costumes"],
    "Rings": ["Bracelets", "Earrings", "Necklaces"],
    "Socks": ["Onesies", "Hoodies", "Tops"],
    "Tops": ["Hoodies", "Socks", "Onesies"],
    
    "Homeware": ["Art Prints", "Calendars", "Custom Ferret Portrait"],
    "Art Prints": ["Custom Ferret Portrait", "Calendars", "Wall Decals"],
    "Calendars": ["Diaries & Notebooks", "Art Prints", "Custom Ferret Portrait"],
    "Cushions & Bedding": ["Bedding & Blankets", "Travel Bedding", "Lifestyle Subscription"],
    "Custom Ferret Portrait": ["Art Prints", "Calendars", "Wall Decals"],
    "Keychains": ["Phone Cases", "Bracelets", "Necklaces"],
    "Phone Cases": ["Keychains", "Custom Ferret Portrait", "Plates & Mugs"],
    "Plates & Mugs": ["Cushions & Bedding", "Wall Decals", "Lifestyle Subscription"],
    "Stationery": ["Diaries & Notebooks", "Pens", "Stickers"],
    "Diaries & Notebooks": ["Calendars", "Pens", "Stickers"],
    "Pens": ["Diaries & Notebooks", "Stickers", "Calendars"],
    "Stickers": ["Diaries & Notebooks", "Pens", "Calendars"],
    "Wall Decals": ["Art Prints", "Custom Ferret Portrait", "Plates & Mugs"],
    "Lifestyle Gift Baskets": ["Cushions & Bedding", "Calendars", "Homeware"],
    "Lifestyle Learn": ["Workshops & Others Courses", "Ferret Training Guides", "Essentials Learn"],
    "Lifestyle Subscription": ["Homeware", "Apparel & Accessories", "Cushions & Bedding"],
    
    "Play & Train": ["Toys", "Play Pens", "Training Aids & Other Tools"],
    "Ferret Training Guides": ["Books & Others Resources", "Clickers", "Harnesses"],
    "Play & Train Gift Baskets": ["Toys", "Treats", "Training Aids & Other Tools"],
    "Play & Train Learn": ["Ferret Training Guides", "Workshops & Others Courses"],
    "Play & Train Subscription": ["Toys", "Training Aids & Other Tools", "Treats"],
    "Play Pens": ["Toys", "Training Aids & Other Tools", "Leashes"],
    "Toys": ["Treats", "Play Pens", "Play & Train Subscription"],
    "Training Aids & Other Tools": ["Clickers", "Harnesses", "Collars"],
    "Books & Others Resources": ["Ferret Training Guides", "Workshops & Others Courses"],
    "Clickers": ["Training Aids & Other Tools", "Harnesses", "Treats"],
    "Collars": ["Harnesses", "Leashes", "Training Aids & Other Tools"],
    "Harnesses": ["Leashes", "Collars", "Training Aids & Other Tools"],
    "Leashes": ["Harnesses", "Collars", "GPS Trackers"],
    "Treats": ["Toys", "Training Aids & Other Tools", "Food"],
    
    "Workshops & Others Courses": ["Ferret Training Guides", "Essentials Learn", "Lifestyle Learn"]
}

# Generate a filename with the current datetime for script logging
log_filename = datetime.now().strftime("automation_%Y-%m-%d_%H-%M-%S.log")

# Check if the log file already exists; if not, create it
if not os.path.exists(log_filename):
    open(log_filename, 'w').close()

# Configure logging
logging.basicConfig(filename=log_filename, level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Commence Product Listing script logging
currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logging.info(f"Script started at {currentDateTime}.")

# Upload OPEN AI Variables
try:
    logging.info("Setting OpenAI Variables...")
    import api_key_variable
    #OpenAI Variable
    openai.api_key = api_key_variable.API_KEY_VARIABLE
    ORGANIZATION_ID = api_key_variable.ORGANIZATION_ID
    PROJECT_ID = apy_key_variable.PROJECT_ID
    Assistant_ID = api_key_variable.Assistant_ID
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully set Open AI variables at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to set OpenAI variables at {currentDateTime}: {str(e)}")
    raise
"""do I need the following inserted in the above passage?"""
url = https://api.openai.com/v1/assistants/{Assistant_ID} \

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY_VARIABLE}",
    "OpenAI-Beta": "assistants=v2",
    "OpenAI-Organization": "{ORGANIZATION_ID}",
    "OpenAI-Project": PROJECT_ID
}

response = requests.get(url, headers=headers)

"""finish this to associate id with the assistant on open ai"""
#RETRIEVE ASSISTANT 
from openai import OpenAI
client = OpenAI()

my_assistant = client.beta.assistants.retrieve("asst_abc123")
print(my_assistant)

"""finish off checking on assistant by retrieving it's details at the start of the process"""
# print to logs at start of work
#RETRIEVE ASSISTANT 
from openai import OpenAI
client = OpenAI()

my_assistant = client.beta.assistants.retrieve("{Assistant_ID}")
print(my_assistant)




"""# Load the products_catalog CSV file
try:
    logging.info("Loading the products_catalog CSV...")
    df = pd.read_csv('products_catalog.csv', encoding='utf-8')
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully loaded products_catalog CSV file at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to load products_catalog CSV file at {currentDateTime}: {str(e)}")
    raise

# Convert the products_catalog to JSON
try:
    logging.info("Converting products_catalog to JSON...")
    json_output = df.to_json(orient='records', lines=True)
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully converted products_catalog to JSON at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to convert products_catalog to JSON at {currentDateTime}: {str(e)}")
    raise

# Save the products_catalog to a JSON file
try:
    logging.info("Converting products_catalog to JSON...")
    with open("/mnt/data/Product_Catalog.json", "w") as json_file:
        json_file.write(json_output)
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully saved products_catalog to JSON at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to save products_catalog to JSON at {currentDateTime}: {str(e)}")
    raise"""

# Load the SKU_checklist CSV file 
try:
    logging.info("Loading the SKU_Checklist CSV...")
    df = pd.read_csv('SKU_Checklist.csv', encoding='utf-8')
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully loaded SKU_Checklist CSV file at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to load SKU_Checklist CSV file at {currentDateTime}: {str(e)}")
    raise

# Convert SKU_checklist to JSON
try:
    logging.info("Converting SKU_Checklist to JSON...")
    json_output = df.to_json(orient='records', lines=True)
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully converted SKU_Checklist to JSON at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to convert SKU_Checklist to JSON at {currentDateTime}: {str(e)}")
    raise

# Save SKU_checklist to a JSON file
try:
    logging.info("Converting products_catalog to JSON...")
    with open("/mnt/data/Product_Catalog.json", "w") as json_file:
        json_file.write(json_output)
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully saved products_catalog to JSON at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to save products_catalog to JSON at {currentDateTime}: {str(e)}")
    raise

# Upload JSON files to OpenAI Assistant
Vector upload instructions


"""
# Create a vector store called "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Financial Statements")
 
# Ready the files for upload to OpenAI
file_paths = ["edgar/goog-10k.pdf", "edgar/brka-10k.txt"]
file_streams = [open(path, "rb") for path in file_paths]

a sku library of products
	added to OpenAI Assistant as context 
	product_catalog
        
        #Create a vector store and add files;
vector_store = client.beta.vector_stores.create(
  name="Product Documentation",
  file_ids=['file_1', 'file_2', 'file_3', 'file_4', 'file_5']
)
Adding files to vector stores is an async operation. To ensure the operation is complete, we recommend that you use the 'create and poll' helpers in our official SDKs. If you're not using the SDKs, you can retrieve the vector_store object and monitor it's file_counts property to see the result of the file ingestion operation.
Files can also be added to a vector store after it's created by creating vector store files.

#Attaching a vector store to your assistant 
assistant = client.beta.assistants.create(
  instructions="You are a helpful product support assistant and you answer questions based on the files provided to you.",
  model="gpt-4o",
  tools=[{"type": "file_search"}],
  tool_resources={
    "file_search": {
      "vector_store_ids": ["vs_1"]
    }
  }
)

thread = client.beta.threads.create(
  messages=[ { "role": "user", "content": "How do I cancel my subscription?"} ],
  tool_resources={
    "file_search": {
      "vector_store_ids": ["vs_2"]
    }
  }
)

        
        """
#update the assistant to use new vector store 
assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)





# Create function for verifing if a product listing should be generated or not 
"""python to check json"""


# Load the CSV file containing product listings using the pandas module
try:
    logging.info("Loading the CSV with pandas module...")
    df = pd.read_csv('Productlisting.csv', encoding='utf-8')
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully loaded CSV file with {len(df)} products at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to load CSV file at {currentDateTime}: {str(e)}")
    raise

# Open the CSV file for reading and manipulating
try:
    logging.info("Opening the CSV for reading and writing...")
    productListingFile = open("Productlisting.csv", mode="r+", encoding="utf-8")
    next(productListingFile)
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info(f"Successfully opened CSV file at {currentDateTime}")
except Exception as e:
    currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.error(f"Failed to open CSV file at {currentDateTime}: {str(e)}")
    raise



# Get the total number of products in the DataFrame
dfLength = len(df)
count = 0

# Function to get a chat completion from OpenAI
def getChatCompletions(requestMessageContent):
    try:
        logging.info("Getting chat completion...")
        responseName = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": marketingPersonality},
                {"role": "user", "content": requestMessageContent}
            ]
        )
        responseValue = responseName.choices[0].message.content
        
        # Log the time of the response
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully received response from OpenAI at {currentDateTime}")	
        return responseValue
    except Exception as e:
        # Log the error with the current time
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate completion at {currentDateTime}: {str(e)}")
        raise
"""Relevant?
#SETUP STREAM CHAT
with client.beta.threads.runs.stream(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account.",
  event_handler=EventHandler(),
) as stream:
  stream.until_done()
"""
"""
#CREATE A RUN 
https://platform.openai.com/docs/api-reference/runs/createRun
"""
"""all vector stores from this point should be saved to the thread and logged
#attach a file to a message thread instead
# Upload the user provided file to OpenAI
message_file = client.files.create(
  file=open("edgar/aapl-10k.pdf", "rb"), purpose="assistants"
)
 
# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": "How many shares of AAPL were outstanding at the end of of October 2023?",
      # Attach the new file to the message.
      "attachments": [
        { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
      ],
    }
  ]
)
 
# The thread now has a vector store with that file in its tool resources.
print(thread.tool_resources.file_search)"""
"""#Test file search is working properly: Your new assistant will query both attached vector stores (one containing goog-10k.pdf and brka-10k.txt, and the other containing aapl-10k.pdf) and return this result from aapl-10k.pdf
# Use the create and poll SDK helper to create a run and poll the status of
# the run until it's in a terminal state.

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

message_content = messages[0].content[0].text
annotations = message_content.annotations
citations = []
for index, annotation in enumerate(annotations):
    message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
    if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"[{index}] {cited_file.filename}")

print(message_content.value)
print("\n".join(citations))

"""

# Loop through each row in the DataFrame to process product listings
for index, product in enumerate(productListingFile.readlines()):
    try:
        logging.info("Looping the DataFrame...")
        # Split up the rows into a list containing a different set of data for each column
        product = product.split(",")
        
        # If statement to make sure the for loop runs between the number of rows in the file only
        if count <= dfLength-1:
            productSKU = product [0]
            productType = product[1]
            productName = product[3]
            productPublished = product[4]
            productFeatured = product[5]
            productSDescription = product[7]
            productLDescription = product[8]
            productWeight = product[18]
            productLength = product[19]
            productWidth = product[20]
            productHeight = product[21]
            productReviews = product[22]
            productPurchaseNote = product [23]
            productPrice = product[25]
            productCategories = product[26]
            productTags = product[27]
            productShippingClass = product[28]
            productImages = product[29]
            productUpsell = product[34]
            productCross = product[35]
            productAttributeOneName = product[39]
            productAttributeOneDesc = product[40]
            productAttributeTwoName = product[46]
            productAttributeTwoDesc = product[47]
            productAttributeThreeName = product[53]
            productAttributeThreeDesc = product[54]
            product = product[75]
            
            # Log success of processing for this product
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Successfully processed product {index + 1}: {productName} at {currentDateTime}")
        else:
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.warning(f"Product processing skipped {index + 1} due to index out of range at {currentDateTime}")
    except Exception as e:
        # Log any errors that occur during the processing of this product
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to process product {index + 1} at {currentDateTime}: {str(e)}")
        continue

    count += 1  # Increment the count for the next iteration
"""Modify the above with:
#create a thread (that will run from variable to last variation for each SKU) then another new thread
thread = client.beta.threads.create()

thread should open with the first variable then close with the last variant offered (use productType)

#add a message to the thread
message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
)

Next: Create a Run
Once all the user Messages have been added to the Thread, you can Run the Thread with any Assistant. Creating a Run uses the model and tools associated with the Assistant to generate a response. These responses are added to the Thread as assistant Messages.

#create a run
run = client.beta.threads.runs.create_and_poll(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account."
)

#list the messages
if run.status == 'completed': 
  messages = client.beta.threads.messages.list(
    thread_id=thread.id
  )
  print(messages)
else:
  print(run.status)

"""
    # Generate a product name with specific formatting requirements, using the function
    try:
        logging.info("Generating product name...")
        generatedProductNameMessage = f"""Write a unique title aimed at all pet owners but primarily appealing to ferret lovers.
        \n The product name includes the product variant size or sizes available; S, M, and L denoting small, medium, and large and color or colors the item is in.
        \n It also may include information regarding whether or not it is a single item or a set, return only the product name, the size, the color, and if it is a part of a set.
        \n Mention set only if it is a part of a set, mention nothing regarding set or single piece otherwise.
        \n {productName}"""
        resultName = getChatCompletions(generatedProductNameMessage)
        print(f"{resultName}\n\n")
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully generated product name for {productName} at {currentDateTime}")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate product name for {productName} at {currentDateTime}: {str(e)}")
        continue
    
    # Generate a short description for the product
    try:
        logging.info("Generating short description...")
        responseProductSDescription = f"""Write a short marketing spiel for the product aimed at all pet owners but primarily appealing to ferret lovers.
        \n This should only be 2 sentences long. The response should include only the 2 sentences requested.
        \n {resultName}"""
        resultProductSDescription = getChatCompletions(responseProductSDescription)
        print(f"{resultProductSDescription}\n\n")
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully generated short description for {productName} at {currentDateTime}")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate short description for {productName} at {currentDateTime}: {str(e)}")
        continue

    # Generate Product Categories
    try:
        logging.info("Generating product categories...")
        
        # Find a matching category from the category_map based on the product name
        category_key = None
        for key in category_map:
            if key in productName.lower():  # Assuming productName contains the name of the product
                category_key = key
                break
    
        if category_key:
            resultProductCategories = " > ".join(category_map[category_key])
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Matched product '{productName}' with category '{resultProductCategories}' using key '{category_key}' at {currentDateTime}")
        else:
            responseProductCategories = f"""Use any and all relevant information to assess the appropriate product Categories. All products must have a For Ferrets or For Humans tag, as well as a primary Category. If the primary Category is as a sub-category, then all Categories from superior Categories must also be listed. For example, if product is a Leash, Categories must include Play & Train, Training Aids & Other Tools, Leashes, For Ferrets, or if product is Wall Decal, Categories should be Lifestyle, Homeware, Wall Decals, For Humans.
            \n Output must then be formatted according to the Category Map. Return only in this format. No product description or long form text should be output.
            \n {category_map}, {resultName}, {resultProductSDescription}, {productLDescription}, {productLength}, {productWidth}, {productHeight}, {productSize}, {productColors}, {productCategories}"""
            resultProductCategories = getChatCompletions(responseProductCategories)
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated product categories via OpenAI for {productName} at {currentDateTime}")
            print(f"{resultProductCategories}\n\n")
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Successfully generated product categories for {productName} at {currentDateTime}")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate product categories for {productName} at {currentDateTime}: {str(e)}")
        continue
    
    # Generate Product Tags
    try:
        logging.info("Generating product tags...")
        responseProductTags = f"""Use any and all relevant information to assess the appropriate product Tags. All products must have a For Ferrets or For Humans tag, as well as all relevant additional tags. There is no tag hierarchy or limit on number of tags a product can have, however if a tag matches a category from the Category_Map then the tag output must include at a minimum all listed categories as comma separated tags e.g. "leash": "For Ferrets", "Play & Train", "Training Aids & Others Tools", 'Leashes". All tags should be output as a csv string.
        \n This is the list of available tags: About, Access Steps, Adventure, Apparel & Accessories, Art Prints, Bedding & Blankets, Behavior & Welfare, behavior and welfare, Books & Others Resources, Bracelets, Bundles, Kits and Gift Baskets, Cage, Cage Rage, Cages, Calendars, Carry Cases & Bags, Clickers, Collars, Common Diseases, Comparative Medicine & Biomedical Research, Conservation & Ecology, Costumes, Cushions & Bedding, Custom Ferret Portrait, Diaries & Notebooks, Digital Devices, Digital Monitoring Devices, Diseases & Health Issues, DIY, Earrings, Essentials, Ferret Costumes, Ferret Lifespan Research Project, Ferret Treats, FLRP, Food, Food & Water Bowls, For Ferrets, For Humans, Genetics & Breeding, GPS Trackers, Grooming, Grooming Tools, Hair Pieces, Harnesses, History, Home & Personal Items, Hoodies, Keychains, Kibble Diet, Learn, Leashes, Lifestyle, Litter Trays, Meat, Necklaces, Nutrition, Onesies, Pens, Phone Cases, Plates & Mugs, Play & Train, Play Pens, Policy, Raw, Raw Diet, Raw Food, Raw Meat Diet, Rings, Socks, Stationary, Stickers, Subscription Services, T-Shirts, Toys, Training Aids and Other Tools, Treats, Veterinary Medicine, Veterinary Medicine & Animal Health, Wall Decals, Workshops & Other Courses, Uncategorised.
        \n {category_map}, {resultName}, {resultProductSDescription}, {productLDescription}, {productLength}, {productWidth}, {productHeight}, {productSize}, {productColors}, {productCategories}"""
        resultProductTags = getChatCompletions(responseProductTags)
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Generated product tags via OpenAI for {productName}")
        print(f"{resultProductTags}\n\n")		    
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully generated product tags for {productName} at {currentDateTime}")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate product tags for {productName} at {currentDateTime}: {str(e)}")
        continue
    
    # Generate Attributes
    try: 
        logging.info("Generating attributes...")
    
        # Gather existing data from the product fields
        existing_data = {
            "AttributeOneName": productAttributeOneName,
            "AttributeOneDesc": productAttributeOneDesc,
            "AttributeTwoName": productAttributeTwoName,
            "AttributeTwoDesc": productAttributeTwoDesc,
            "AttributeThreeName": productAttributeThreeName,
            "AttributeThreeDesc": productAttributeThreeDesc,
        }
    
        # Craft a message to OpenAI
        responseProductAttributes = f"""Use any and all relevant information to assess the 3 most relevant and useful product attributes from the available attributes shown in the attributes_map and/or based on best assessment of the product.
        There may be information already present in the field. You are not to erase or replace this data; you are only allowed to fill in the empty attribute fields available. You are to choose the 3 best attributes available to represent the item.
        You will be given any existing information and must include it in the output you create.
        \nExisting data: {existing_data}
        \nProduct Information: {resultName}, {resultProductSDescription}, {ProductLDescription}, {resultProductLength}, {resultProductWidth}, {resultProductHeight}, {resultProductSize}, {resultProductWeight}, {resultProductCategories}"""
    
        # Get AI response
        resultProductAttributes = getChatCompletions(responseProductAttributes)
    
        # Assign the AI-generated attributes to the relevant fields
        productAttributeOneName = resultAttributes.get("AttributeOneName", productAttributeOneName)
        productAttributeOneDesc = resultAttributes.get("AttributeOneDesc", productAttributeOneDesc)
        productAttributeTwoName = resultAttributes.get("AttributeTwoName", productAttributeTwoName)
        productAttributeTwoDesc = resultAttributes.get("AttributeTwoDesc", productAttributeTwoDesc)
        productAttributeThreeName = resultAttributes.get("AttributeThreeName", productAttributeThreeName)
        productAttributeThreeDesc = resultAttributes.get("AttributeThreeDesc", productAttributeThreeDesc)
    
        # Log the success of attribute generation
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully generated attributes for {productName} at {currentDateTime}")
    
        # Log the recommended updates to the attributes_map
        for key, value in resultAttributes.items():
            if key not in attributes_map or value not in attributes_map.get(key, []):
                logging.info(f"Recommended Attribute_Map Update: {key} = {value}")
                
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate attributes for {productName} at {currentDateTime}: {str(e)}")
        continue

    # Function to find Upsell Products
    try:
        logging.info("Generating Upsell opportunities...")
        responseProductUpsell = f"""Choose 2-4 products from The Dookery's product catalog to Upsell (this function identifies complementary products within a similar price range). 
        \n Use the Complementary_Map to determine which product categories to choose products from.
        \n Then use the product catalog to find products with the selected categories with a price point between 0.8 * price, and 1.5 * price and list them.
        \n Then sort the identified products list by Popularity and Reviews.
        \n Where there is no useful information to determine an outcome, use your own logic to select appropriate complementary Upsell products from the product catalog.
        \n Choose the top 2-4 products to output. The response should include product SKU only, output in comma-separated string form.
	\n {product_catalog}, {complementary_map}, {resultName}, {resultProductSDescription}, {productCategories}, {productPrice}, """
	
        # Get the completion from OpenAI
        resultProductUpsell = getChatCompletions(responseProductUpsell)
        
        # Log the successful generation
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Generated Upsell via OpenAI for {productName} at {currentDateTime}")
        print(f"{resultProductUpsell}\n\n")
        
    except Exception as e:
        # Log any errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate product upsell for {productName} at {currentDateTime}: {str(e)}")
        continue
    
    # Function to find Cross-Sell Products
    try:
        logging.info("Generating CrossSell opportunities...")
        responseProductCross = f"""Choose 2-4 products from The Dookery's product catalog to Cross-Sell (this function identifies complementary products lower in price).
        \n Use the Complementary_Map to determine which product categories to choose products from.
        \n Then use the product catalog to find products with the selected categories with a price point between 0.8 * price, and 1.5 * price and list them.
        \n Then sort the identified products list by Popularity and Reviews.
        \n Where there is no useful information to determine an outcome, use your own logic to select appropriate complementary Cross-Sell products from the product catalog.
        \n Choose the top 2-4 products to output. The response should include product SKU only, output in comma-separated string form."""
        
        # Get the completion from OpenAI
        resultProductCross = getChatCompletions(responseProductCross)
        
        # Log the successful generation
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Generated Cross-Sell via OpenAI for {productName} at {currentDateTime}")
        print(f"{resultProductCross}\n\n")
        
    except Exception as e:
        # Log any errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate product cross sell for {productName} at {currentDateTime}: {str(e)}")
        continue
    
# Confirm or find Height
def find_or_confirm_height(productHeight, productLDescription, productAttributes, productName):
    try:
        logging.info("Assessing height...")
        
        # Check if height is already present
        if pd.notnull(productHeight) and productHeight > 0:
            logging.info("Height is already present in the CSV.")
            return productHeight
        else:
            logging.info("Height not present, querying OpenAI for height assessment...")

            # OpenAI query to determine the height from description and attributes
            responseProductHeight = f"""Determine the height of the product from the following details:
            \n Description: {productLDescription}
            \n Attributes: {productAttributes}
            \n Provide only the height value in cm or inches. Ensure height is specific to the product variant contained in the product listing. Return in string format."""
            
            # Get the response from OpenAI
            resultProductHeight = getChatCompletions(responseProductHeight)       
    
            # Log the successful generation
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated Height via OpenAI for {productName} at {currentDateTime}")
            print(f"Height for {productName}: {resultProductHeight}\n")
            
            return resultProductHeight
    
    except Exception as e:
        # Log any errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm height for {productName} at {currentDateTime}: {str(e)}")
        return None

# Confirm or find Length
def find_or_confirm_length(productLength, productLDescription, productAttributes, productName):
    try:
        logging.info("Assessing length...")
        
        # Check if length is already present
        if pd.notnull(productLength) and productLength > 0:
            logging.info("Length is already present in the CSV.")
            return productLength
        else:
            logging.info("Length not present, querying OpenAI for length assessment...")

            # OpenAI query to determine the length from description and attributes
            responseProductLength = f"""Determine the length of the product from the following details:
            \n Description: {productLDescription}
            \n Attributes: {productAttributes}
            \n Provide only the length value in cm or inches. Ensure length is specific to the product variant contained in the product listing. Return in string format."""
            
            # Get the response from OpenAI
            resultProductLength = getChatCompletions(responseProductLength)       
    
            # Log the successful generation
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated Length via OpenAI for {productName} at {currentDateTime}")
            print(f"Length for {productName}: {resultProductLength}\n")
            
            return resultProductLength 
    
    except Exception as e:
        # Log any errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm length for {productName} at {currentDateTime}: {str(e)}")
        return None    

# Confirm or find Width
def find_or_confirm_width(productWidth, productLDescription, productAttributes, productName):
    try:
        logging.info("Assessing width...")
        
        # Check if width is already present
        if pd.notnull(productWidth) and productWidth > 0:
            logging.info("Width is already present in the CSV.")
            return productWidth
        else:
            logging.info("Width not present, querying OpenAI for width assessment...")

            # OpenAI query to determine the width from description and attributes
            responseProductWidth = f"""Determine the width of the product from the following details:
            \n Description: {productLDescription}
            \n Attributes: {productAttributes}
            \n Provide only the width value in cm or inches. Ensure width is specific to the product variant contained in the product listing. Return in string format."""
            
            # Get the response from OpenAI
            resultProductWidth = getChatCompletions(responseProductWidth)       
    
            # Log the successful generation
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated Width via OpenAI for {productName} at {currentDateTime}")
            print(f"Width for {productName}: {resultProductWidth}\n")
            
            return resultProductWidth 
    
    except Exception as e:
        # Log any errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm width for {productName} at {currentDateTime}: {str(e)}")
        return None
    
# Confirm or find Weight
def find_or_confirm_weight(productWeight, productLDescription, productAttributes, productName):
    try:
        logging.info("Assessing weight...")
        
        # Check if weight is already present
        if pd.notnull(productWeight) and productWeight > 0:
            logging.info("Weight is already present in the CSV.")
            return productWeight
        else:
            logging.info("Weight not present, querying OpenAI for weight assessment...")

            # OpenAI query to determine the weight from description and attributes
            responseProductWeight = f"""Determine the weight of the product from the following details:
            \n Description: {productLDescription}
            \n Attributes: {productAttributes}
            \n Dimensions: {productHeight}, {ProductLength}, {ProductWidth}
            \n If weight metric is otherwise unavailable, determine approximate weight by calculating objects volume. If this path is taken, weight MUST be marked '"approx."
            \n Provide only the weight value in grams or kilograms. Ensure weight is specific to the product variant contained in the product listing. Return in string format."""
            
            # Get the response from OpenAI
            resultProductWeight = getChatCompletions(responseProductWeight)
    
            # Log the successful generation
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated Weight via OpenAI for {productName} at {currentDateTime}")
            print(f"Weight for {productName}: {resultProductWeight}\n")
            
            return resultProductWeight
    
    except Exception as e:
        # Log any errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm weight for {productName} at {currentDateTime}: {str(e)}")
        return None
 
    # Generate Shipping Class
    """width, length, height, weight
    need a postage matrix
    
   # Function to classify product based on weight and dimensions
def classify_product(weight, length, width, height):
    try:
        logging.info("Classifying shipping class based on weight and dimensions...")

        # Calculate total dimension (sum of all dimensions)
        total_dimension = length + width + height

        # Calculate volume for additional considerations (assuming cubic cm)
        volume = length * width * height

        # Define classification logic
        if weight <= 0.5 and total_dimension <= 60:
            shipping_class = "Light"
        elif (0.5 < weight <= 5) or (60 < total_dimension <= 150):
            shipping_class = "Medium"
        elif volume > 100000 or any(dim > 100 for dim in [length, width, height]):
            # Assuming that any dimension over 100 cm or a volume over 100,000 cubic cm makes the product oversized
            shipping_class = "Oversized"
        else:
            shipping_class = "Heavy"

        logging.info(f"Product classified as: {shipping_class}")
        return shipping_class
    
    except Exception as e:
        logging.error(f"Failed to classify product shipping class: {str(e)}")
        return None

# Example usage within your product processing loop
for index, row in df.iterrows():
    try:
        productName = row['Product Name']
        productWeight = row['Weight']
        productLength = row['Length']
        productWidth = row['Width']
        productHeight = row['Height']

        logging.info(f"Processing shipping class for product {index + 1}: {productName}")

        # Confirm or find the dimensions and weight
        confirmed_weight = find_or_confirm_weight(productWeight, row['Product Description'], row['Product Attributes'], productName)
        confirmed_length = find_or_confirm_length(productLength, row['Product Description'], row['Product Attributes'], productName)
        confirmed_width = find_or_confirm_width(productWidth, row['Product Description'], row['Product Attributes'], productName)
        confirmed_height = find_or_confirm_height(productHeight, row['Product Description'], row['Product Attributes'], productName)

        # Classify the shipping class
        shipping_class = classify_product(confirmed_weight, confirmed_length, confirmed_width, confirmed_height)
        df.at[index, 'Shipping Class'] = shipping_class
        logging.info(f"Shipping class updated for product {productName}: {shipping_class}")
        
    except Exception as e:
        logging.error(f"Failed to process shipping class for product {index + 1}: {str(e)}")
        continue

# Save the updated DataFrame back to the CSV
try:
    df.to_csv('Productlisting_updated.csv', index=False, encoding='utf-8')
    logging.info("Updated CSV file with shipping classes saved successfully.")
except Exception as e:
    logging.error(f"Failed to save the updated CSV file with shipping classes: {str(e)}")
    """
    
    
    # Generate a detailed long description for the product
    try:
        logging.info("Generating long description...")
        if productType == "variable":
            responseProductLDescription = f"""You are going to be given a product name, product short description, product long description, product length, product width, product height, product weight, product shipping class, product attributes (size, color, style, capacity, specification), product categories and product tags for context.
            \n Use any and all relevant information to create a detailed and organised product listing for The Dookery's website.
            \n The listing should include the following 3 components: Introduction, Specifications, and The Dookery's Tips & Tricks for Ferret Lovers.
            \n Introduction component must include the following:
            \n A catchy descriptive title that clearly identifies the product and its primary benefits.
            \n A compelling opening sentence that highlights the key features and benefits of the product for any animal owner or animal lover that utilises friendly and engaging language to draw in the reader and focuses on how the product can improve the lives of animals and/or their owners.
            \n An engaging paragraph that introduces the product, mentioning its primary purpose/s and essential qualities, intended use, how the product enhances the target audience's experience, and overall benefits, emphasizing convenience, style, and any unique features that set the product apart.
            \n A paragraph outlining general product information including details of all variations and specifications listed (e.g. size, color, etc), placing emphasis on matching product specific details to the usability of the product for all pet owners in particular ferret owners and lovers, offering a list of common animals the product is appropriate (must include ferrets) and inappropriate for, and how many animals the product is appropriate for (e.g. 1 dog, 3 ferrets, 1 human).
            \n Specifications component must include the following: Product Name, Suitable Animals, Material/s, Dimensions (Length x Width x Height), Weight, Features, Product Safety Warnings, and any other Notable Features (Color, Size, Style, Capacity). Present Specifications as a uniform and formatted grid/table. Every row and column should be of the same length, width and height.
            \n The Dookery's Tips & Tricks for Ferret Lovers component must include the following:
            \n Component header.
            \n Practical advice on how to effectively utilize the product with a ferret/s to achieve optimal usage (if the product is For Ferrets), or for optimal usage for a human (if the product is For Humans). This can include tips on color selection, placement, maintenance, cleaning, integration with other products, and integration into existing setups.
            \n Product Pros: a bulletpoint list of honest product Pros (advantages) for a ferret or ferret owner listing the primary advantages of the product as well as highlighting aspects like durability, design, ease of use, functionality, and any unique features that make the product stand out.
            \n Product Cons: a bulletpoint list of honest but balanced product Cons (disadvantages) for a ferret or ferret owner listing any potential drawbacks or considerations to keep in mind and mentioning aspects like maintenance requirements or size constraints that customers should be aware of before purchasing.
            \n Product Use Warnings: a brief section outlining all recommendations for safe and effective use of the product for a ferret owner or ferret lover, including precautions or warnings specific to each variant, handling instructions, cleaning advice, placement advice, safe handling, and guidance on how to perform maintenance checks to ensure the product remains safe and functional in order to provide a safe environment for your ferrets.
            \n Lastly a wrap up paragraph with an encouraging statement that reinforces the product's value and why it's a smart and essential addition to the customers household and their ferret's environment.
            \n Preserve all image data given to you in the Description field and insert it into the output created. Do not remove any image data from the product Description. Use data from productImages field for context in creating description.
            \n Apply the following html standards to output created: Wrap each section in <p> tags for proper paragraph separation, Use <b> tags for headings or important text, Implement lists with <ul> and <li> tags when listing multiple items, Embed images using <img> tags with appropriate src and style attributes, Use <br> tags for line breaks within paragraphs where needed, Nest elements appropriately to maintain clean structure and readability, Use non-breaking spaces to control spacing and formatting where needed, Use HTML tags consistently.
            \n Return in string form.
            \n {productImages}, {resultName}, {resultProductSDescription}, {productLDescription}, {productLength}, {productWidth}, {productHeight}, {productSize}, {productColors}, {productCategories}"""
            resultProductLDescription = getChatCompletions(responseProductLDescription)
            print(f"{resultProductLDescription}\n\n")
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Update LDescription variable and log
            df.loc[count, 'Description'] = resultProductLDescription
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Successfully generated new long description for {productName} at {currentDateTime}")
        else:
            # Existing variable retained for variant listings and logged
            df.loc[count, 'Description'] = resultProductLDescription
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Successfully saved existing long description for {productName} at {currentDateTime}")
    except Exception as e:
        # Log errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate long description for {productName} at {currentDateTime}: {str(e)}")
        continue







    # Write a Purchase Note
    try:
        logging.info("Updating purchase note...")
        responsePurchaseNote = f"""Craft a Purchase Note for the buyer of this product. 
        The Purchase Note can be used for various purposes, such as providing additional information about the product, offering instructions for using the product, sharing a thank you message or a link to download digital products, and giving details about how the customer can contact The Dookery for support or further inquiries (by email admin@dookery.com). If the product includes special instructions, download links, or personalized messages that should be conveyed to the buyer post-purchase, the Purchase Note field is a convenient place to include that information. 
        You need to apply a rational mind and be sparse in what information you offer here. It needs to be specific to the exact variant being purchased. A customer may purchase multiple items and does not need to see identical thank you messages after every purchase. If you have nothing useful to add here, leave this field blank.
        \nProduct Name: {resultName}\nShort Description: {resultProductSDescription}\nLong Description: {resultProductLDescription}"""
        resultPurchaseNote = getChatCompletions(responsePurchaseNote)
    
        # Log the success of OpenAI completion
        print(f"{resultPurchaseNote}\n\n")     
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully generated Purchase Note via OpenAI for {productName} at {currentDateTime}")
    except Exception as e:
        # Log the failure in generating the Purchase Note
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate Purchase Note for {productName} at {currentDateTime}: {str(e)}")
        continue

    # Enable customer reviews for the product
    try:
        logging.info("Enabling customer reviews...")
        # Assuming you want to set a flag in the DataFrame to enable reviews
        resultProductReviews = 1  # This value indicates that reviews are enabled
        print(f"Customer reviews enabled: {resultProductReviews}\n\n-----\n\n")
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully enabled customer reviews for {productName} at {currentDateTime}")
    except Exception as e:
        # Log any errors that occur
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to enable customer reviews for {productName} at {currentDateTime}: {str(e)}")
        continue

    # Update published status for the product
    try:
        logging.info("Updating published state...")
        resultProductPublished = 1
        print(f"{resultProductPublished}\n\n-----\n\n")
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully updating published status for {productName} at {currentDateTime}")
    except Exception as e:
        # Log errors
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to update published status for {productName} at {currentDateTime}: {str(e)}")
        continue

# Image Functions
"""
#Editing image files
https://platform.openai.com/docs/api-reference/authentication

#upload image files
https://platform.openai.com/docs/api-reference/files/create\

Marketing image manipulation (maybe through modular mind?): back ground removal, ferret themed, drm
	Index your existing ferret media library and create logs of existing usage


"""






"""#List messages in the thread
get https://api.openai.com/v1/threads/{thread_id}/messages

Returns a list of messages for a given thread.

from openai import OpenAI
client = OpenAI()

thread_messages = client.beta.threads.messages.list("thread_abc123")
print(thread_messages.data)


"""

# Generate Suggested Price Point 
Add profit to price

# Generate Price Point Feedback
Will a customer come to you over someone else for this reason?
Could the price be adjusted upwards while remaining competitive? 
If the product doesnt compete on price point, can you offer other benefits?

# Generate Market Competitiveness 
How do Pet Barn, Pet Circle, Ebay, Amazon, etc compare.

# Generate Direct Marketing Plan
who (potentially could be appealed to and how), 
the lifestyle side makes the dookery different so lean in
how will purchasing this product encourage customer loyalty 
consider what do ferret owners do and how can this product be marketed to them alternatively? how can I access these people with this product?

# Listing Review
Evaluate listing for flaws and potential fixes, make recomendations 

# Generate Learn Marketing 
Blog and social media ideas, suggesting existing articles to attach the product to

# Generate philanthropy
opportunties to enhance ferret lifespan or the FLRP through the product; how does or can this product help?

# Generate General Marketing Plan
tips, tricks, insights based on market research

# Generate legal: Evaluate for professional indemnity, product design or application risks, as well as potential postal issues due to the nature of the product (e.g. places it can't be imported, etc)

# Generate featured products
"""Featured: if product is good value (variable) 
				feature it
		Value = price is close or below RRP for the same or similar products with reasonably similar features (library of products and 				reference web search through open AI 
		and/or 
		Value = There is no other items with these features on the market (unique) (web search through open AI)"""





    # Update the DataFrame with the generated content
    try:
        logging.info("Updating data frame...")
        df.loc[count, 'Name'] = resultName
        df.loc[count, 'Short description'] = resultProductSDescription
        df.loc[count, 'Categories'] = resultProductCategories
        df.loc[count, 'Tags'] = resultProductTags
        df.loc[count, 'Upsell'] = resultProductUpsell
        df.loc[count, 'Cross'] = resultProductCross
        df.loc[count, 'Height'] = resultProductHeight
        df.loc[count, 'Length'] = resultProductLength
        df.loc[count, 'Width'] = resultProductWidth
        df.loc[count, 'Weight'] = resultProductWeight
        df.loc[count, 'Description'] = resultProductLDescription
        df.loc[count, 'Attribute One Name'] = resultproductAttributeOneName
        df.loc[count, 'Attribute One Description'] = resultproductAttributeOneDesc
        df.loc[count, 'Attribute Two Name'] = resultproductAttributeOneName
        df.loc[count, 'Attribute Two Description'] = resultproductAttributeOneDesc
        df.loc[count, 'Attribute Three Name'] = resultproductAttributeOneName
        df.loc[count, 'Attribute Three Description'] = resultproductAttributeOneDesc
        df.loc[count, 'Purchase Note'] = resultPurchaseNote
        df.loc[count, 'Reviews Enabled'] = resultProductReviews
        df.loc[count, 'Published'] = resultProductPublished

        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully updated DataFrame at {currentDateTime}")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to update DataFrame at {currentDateTime}: {str(e)}")
        continue

    # Save the updated DataFrame to the open CSV file
    try:
        logging.info("Updating CSV file...")        
        df.to_csv("Productlisting.csv", index=False)
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully saved CSV at {currentDateTime}")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to save CSV at {currentDateTime}: {str(e)}")
        continue	    

# End Logging
logging.info("Script complete.")
