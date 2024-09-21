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

# Convert attributes_map to a JSON-formatted string
attributes_map = r"C:\\Users\\LittleChickpea\\Downloads\\attributes_map.json"
attributes_map = json.dumps(attributes_map, indent=2)

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
def initialize_client(openai_api_key):
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

# Function to find or confirm height of the product         
def find_or_confirm_height(openai_api_key, productHeight, productName, productSKU, parent_sku, thread_id, m_assistant_id, client):
    try:
        logging.info(f"Assessing height for product: {productName}")

        # Check if height is already present and valid
        if pd.notnull(productHeight) and productHeight > 0 and 0.5 < productHeight < 300:  # Adding a reasonable range check
            logging.info(f"Height is already present for {productName} in the CSV: {productHeight} cm.")
            return productHeight
        else:
            logging.info(f"Height not present or invalid for {productName}. Querying OpenAI for height assessment...")

            # AI prompts
            responseParentProduct = f"""
                Based on our ongoing discussion, determine the height of this product. 
                If the height is in inches, convert it to centimeters.
                Provide only the height value in numeric format (in cm).
            """

            responseChildProduct = f"""
                Considering this product is a variation of the parent product, and based on the ongoing discussion, determine the height of the product SKU ({productSKU}).
                If the height is mentioned in inches, convert it to centimeters.
                Provide only the height value in numeric format (in cm).
            """

            # Call the getChatCompletions function to get the height using OpenAI
            resultProductHeight = getChatCompletions(
                openai_api_key, None, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
            )

            # Log the successful OpenAI query
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated height for {productName} at {currentDateTime}: {resultProductHeight}")
            print(f"Generated height for {productName}: {resultProductHeight}\n")

            # Validate the result from OpenAI
            try:
                height_value = float(resultProductHeight)
                if 0.5 < height_value < 300:  # Ensure the height is within a reasonable range
                    logging.info(f"Valid height found for {productName}: {height_value} cm.")
                    return height_value
                else:
                    logging.error(f"Invalid height value returned by OpenAI for {productName}: {height_value}")
                    return None
            except ValueError:
                logging.error(f"Failed to convert OpenAI response to a valid number for {productName}. Response: {resultProductHeight}")
                return None

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm height for {productName} at {currentDateTime}: {str(e)}")
        print(f"Failed to find or confirm height for {productName} at {currentDateTime}: {str(e)}")
        return None

# Function to find or confirm Length of the product 
def find_or_confirm_length(openai_api_key, productLength, productName, productSKU, parent_sku, thread_id, m_assistant_id, client):
    try:
        logging.info(f"Assessing length for product: {productName}")

        # Check if length is already present and valid
        if pd.notnull(productLength) and productLength > 0 and 0.5 < productLength < 500:  # Adding a reasonable range check
            logging.info(f"Length is already present for {productName} in the CSV: {productLength} cm.")
            return productLength
        else:
            logging.info(f"Length not present or invalid for {productName}. Querying OpenAI for length assessment...")

            # AI prompts
            responseParentProduct = f"""
                Based on our ongoing discussion, determine the length of this product. 
                If the length is in inches, convert it to centimeters.
                Provide only the length value in numeric format (in cm).
            """

            responseChildProduct = f"""
                Considering this product is a variation of the parent product, and based on the ongoing discussion, determine the length of the product SKU ({productSKU}).
                If the length is mentioned in inches, convert it to centimeters.
                Provide only the length value in numeric format (in cm).
            """

            # Call the getChatCompletions function to get the length using OpenAI
            resultProductLength = getChatCompletions(
                openai_api_key, None, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
            )

            # Log the successful OpenAI query
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated length for {productName} at {currentDateTime}: {resultProductLength}")
            print(f"Generated length for {productName}: {resultProductLength}\n")

            # Validate the result from OpenAI
            try:
                length_value = float(resultProductLength)
                if 0.5 < length_value < 500:  # Ensure the length is within a reasonable range
                    logging.info(f"Valid length found for {productName}: {length_value} cm.")
                    return length_value
                else:
                    logging.error(f"Invalid length value returned by OpenAI for {productName}: {length_value}")
                    return None
            except ValueError:
                logging.error(f"Failed to convert OpenAI response to a valid number for {productName}. Response: {resultProductLength}")
                return None

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm length for {productName} at {currentDateTime}: {str(e)}")
        print(f"Failed to find or confirm length for {productName} at {currentDateTime}: {str(e)}")
        return None

# Function to find or confirm Width of the product
def find_or_confirm_width(openai_api_key, productWidth, productName, productSKU, parent_sku, thread_id, m_assistant_id, client):
    try:
        logging.info(f"Assessing width for product: {productName}")

        # Check if width is already present and valid
        if pd.notnull(productWidth) and productWidth > 0 and 0.5 < productWidth < 500:  # Adding a reasonable range check
            logging.info(f"Width is already present for {productName} in the CSV: {productWidth} cm.")
            return productWidth
        else:
            logging.info(f"Width not present or invalid for {productName}. Querying OpenAI for width assessment...")

            # AI prompt
            responseParentProduct = f"""
                Based on our ongoing discussion, determine the width of this product. 
                If the width is in inches, convert it to centimeters.
                Provide only the width value in numeric format (in cm).
            """

            responseChildProduct = f"""
                Considering this product is a variation of the parent product, and based on the ongoing discussion, determine the width of the product SKU ({productSKU}).
                If the width is mentioned in inches, convert it to centimeters.
                Provide only the width value in numeric format (in cm).
            """

            # Call the getChatCompletions function to get the width using OpenAI
            resultProductWidth = getChatCompletions(
                openai_api_key, None, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
            )

            # Log the successful OpenAI query
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated width for {productName} at {currentDateTime}: {resultProductWidth}")
            print(f"Generated width for {productName}: {resultProductWidth}\n")

            # Validate the result from OpenAI
            try:
                width_value = float(resultProductWidth)
                if 0.5 < width_value < 500:  # Ensure the width is within a reasonable range
                    logging.info(f"Valid width found for {productName}: {width_value} cm.")
                    return width_value
                else:
                    logging.error(f"Invalid width value returned by OpenAI for {productName}: {width_value}")
                    return None
            except ValueError:
                logging.error(f"Failed to convert OpenAI response to a valid number for {productName}. Response: {resultProductWidth}")
                return None

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm width for {productName} at {currentDateTime}: {str(e)}")
        print(f"Failed to find or confirm width for {productName} at {currentDateTime}: {str(e)}")
        return None

# Function to find or confirm Weight of the product
def find_or_confirm_weight(openai_api_key, productWeight, productName, productSKU, parent_sku, productHeight, productWidth, productLength, thread_id, m_assistant_id, client):
    try:
        logging.info(f"Assessing weight for product: {productName}")

        # Check if weight is already present and valid
        if pd.notnull(productWeight) and productWeight > 0 and 0.05 < productWeight < 500:  # Adding a reasonable range check for weight in kg
            logging.info(f"Weight is already present for {productName} in the CSV: {productWeight} kg.")
            return productWeight
        else:
            logging.info(f"Weight not present or invalid for {productName}. Querying OpenAI for weight assessment...")

            # Custom prompt to either provide weight or calculate from dimensions
            responseParentProduct = f"""
                Determine the weight of the product from the information you've already been provided. 
                Focus on the Description and Existing_Data in Attributes for leads.
                
                Provide only the weight value in kg. Value must be converted to kilograms. 
                Ensure the weight is specific to the product variant contained in the product listing. 
                Return in string format.

                If weight metric is otherwise unavailable, determine approximate weight by calculating the object's volume 
                using the Height ({productHeight} cm), Width ({productWidth} cm), and Length ({productLength} cm).
            """

            responseChildProduct = f"""
                Considering this product is a variation of the parent product, determine the weight of the product SKU ({productSKU}).
                Focus on the Description and Existing_Data in Attributes for leads.
                
                Provide only the weight value in kg. Value must be converted to kilograms. 
                Ensure the weight is specific to the product variant contained in the product listing.
                Return in string format.

                If weight metric is otherwise unavailable, determine approximate weight by calculating the object's volume 
                using the Height ({productHeight} cm), Width ({productWidth} cm), and Length ({productLength} cm).
            """

            # Call the getChatCompletions function to get the weight using OpenAI
            resultProductWeight = getChatCompletions(
                openai_api_key, None, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
            )

            # Log the successful OpenAI query
            currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.info(f"Generated weight for {productName} at {currentDateTime}: {resultProductWeight}")
            print(f"Generated weight for {productName}: {resultProductWeight}\n")

            # Validate the result from OpenAI
            try:
                weight_value = float(resultProductWeight)
                if 0.05 < weight_value < 500:  # Ensure the weight is within a reasonable range
                    logging.info(f"Valid weight found for {productName}: {weight_value} kg.")
                    return weight_value
                else:
                    logging.error(f"Invalid weight value returned by OpenAI for {productName}: {weight_value}")
                    return None
            except ValueError:
                logging.error(f"Failed to convert OpenAI response to a valid number for {productName}. Response: {resultProductWeight}")
                return None

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to find or confirm weight for {productName} at {currentDateTime}: {str(e)}")
        print(f"Failed to find or confirm weight for {productName} at {currentDateTime}: {str(e)}")
        return None

def write_purchase_note(openai_api_key, resultName, resultProductSDescription, resultProductLDescription, productName, productSKU, parent_sku, thread_id, m_assistant_id, client):
    try:
        logging.info(f"Updating purchase note for {productName}...")

        # Craft the response for generating a purchase note via OpenAI
        responseParentProduct = f"""
            Craft a Purchase Note for the buyer of this product. The Purchase Note can be used for various purposes, such as providing additional information about the product, offering instructions for using the product, sharing a thank you message or a link to download digital products, and giving details about how the customer can contact The Dookery for support or further inquiries (by email admin@dookery.com). 
            
            If the product includes special instructions, download links, or personalized messages that should be conveyed to the buyer post-purchase, the Purchase Note field is a convenient place to include that information. Apply a rational mind and be sparse in what information you offer here. It needs to be specific to the exact variant being purchased. A customer may purchase multiple items and does not need to see identical thank you messages after every purchase. 
            
            If you have nothing useful to add here, leave this field blank.

            Product Name: {resultName}
            Short Description: {resultProductSDescription}
            Long Description: {resultProductLDescription}
        """

        responseChildProduct = f"""
            Since this product is a variation of the parent product, write a Purchase Note specific to the product SKU ({productSKU}). Consider any special instructions, download links, or personalized messages that should be conveyed to the buyer post-purchase. If you have nothing useful to add here, leave this field blank.

            Product Name: {resultName}
            Short Description: {resultProductSDescription}
            Long Description: {resultProductLDescription}
        """

        # Call getChatCompletions function to get the purchase note
        resultPurchaseNote = getChatCompletions(
            openai_api_key, None, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
        )

        # Log and print the result of the OpenAI call
        print(f"{resultPurchaseNote}\n\n")
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Successfully generated Purchase Note for {productName} at {currentDateTime}")
        
        return resultPurchaseNote

    except Exception as e:
        # Log the failure in generating the Purchase Note
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate Purchase Note for {productName} at {currentDateTime}: {str(e)}")
        print(f"Failed to generate Purchase Note for {productName} at {currentDateTime}: {str(e)}")
        return None

# Extract parent product information for additional context in the API request
def get_attribute_or_unknown(sku, column_name):
    value = extractedparentinfo(sku, column_name, prodf)
    if pd.isna(value) or value == '':
        return "Unknown"
    return value 





# Function to check and update marketing personality
def check_and_update_marketing_personality(m_assistant_id, marketing_personality, client):
    try:
        # Retrieve the current marketing personality from the assistant
        with api_call_lock:
            assistant_details = client.beta.assistants.retrieve(m_assistant_id)
            current_personality = assistant_details.metadata.get("marketing_personality", "").strip()

        print(f"\n def check_and_update_marketing_personality: Assistant Details: {assistant_details}")
        with logging_lock:
            logging.info(f"Assistant Details: {assistant_details}")
        
        # Ensure that both personalities are stripped of extra whitespace and are lowercase for comparison
        marketing_personality_cleaned = marketing_personality.strip().lower()
        current_personality_cleaned = current_personality.lower()

        # Check if the current personality matches the predefined one
        if current_personality_cleaned != marketing_personality_cleaned:
            print("Discrepancy found in marketing personality. Updating assistant...")
            with api_call_lock:
                updated_assistant = client.beta.assistants.update(
                    m_assistant_id,
                    instructions={"marketing_personality": marketing_personality_cleaned},
                )
            print("Marketing personality updated successfully.")
            with logging_lock:
                logging.info(f"Updated marketing personality to: {marketing_personality_cleaned}")
        else:
            print("Marketing personality is up-to-date.")
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to check or update marketing personality at {currentDateTime}: {str(e)}")
        print(f"Failed to check or update marketing personality at {currentDateTime}: {str(e)}")
        raise
 
 # Function to generate Attributes
 def generate_product_attributes(openai_api_key, productSKU, parent_sku, thread_id, m_assistant_id, client, prodf, count, productlisting_file_path, attributes_map, logging):
    try:
        logging.info("Generating Attributes...")
        print("Generating Attributes...")

        # Gather existing data from the product fields
        productAttributes = {
            "AttributeOneName": productAttributeOneName if productAttributeOneName else "Unknown",
            "AttributeOneDesc": productAttributeOneDesc if productAttributeOneDesc else "Details not available",
            "AttributeTwoName": productAttributeTwoName if productAttributeTwoName else "Unknown",
            "AttributeTwoDesc": productAttributeTwoDesc if productAttributeTwoDesc else "Details not available",
            "AttributeThreeName": productAttributeThreeName if productAttributeThreeName else "Unknown",
            "AttributeThreeDesc": productAttributeThreeDesc if productAttributeThreeDesc else "Details not available"
        }

        # Handle None or empty values in productAttributes
        for key, value in productAttributes.items():
            if pd.isna(value) or value == '':
                productAttributes[key] = "N/A"

        # Set xxx variable to productAttributes
        xxx = productAttributes
        logging.info(f"Current productAttributes: {xxx}")
        print(f"Current productAttributes: {xxx}")
                        
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
            "\n Your response should be only the JSON object, and no additional text."
            "\n Example JSON format:"
            "{\n"
            "  \"AttributeOneName\": \"Color\",\n"
            "  \"AttributeOneDesc\": \"Blue\",\n"
            "  \"AttributeTwoName\": \"Size\",\n"
            "  \"AttributeTwoDesc\": \"Medium\",\n"
            "  \"AttributeThreeName\": \"Material\",\n"
            "  \"AttributeThreeDesc\": \"Cotton\"\n"
            "}"
            f"\n Existing product data: {productAttributes}"
            f"\n Existing parent product data: {{'AttributeOneName': '{parentAttributeOneName}', 'AttributeOneDesc': '{parentAttributeOneDesc}', "
            f"'AttributeTwoName': '{parentAttributeTwoName}', 'AttributeTwoDesc': '{parentAttributeTwoDesc}', "
            f"'AttributeThreeName': '{parentAttributeThreeName}', 'AttributeThreeDesc': '{parentAttributeThreeDesc}'}}."
            f"\n Attributes Map: {attributes_map}"
        )

        # Child Product Request
        responseChildProduct = (
            "Remembering that this product is a variation of the parent product, use any and all relevant information to assess the 3 most relevant and useful product attributes "
            "(Name and Description) from the available attributes shown in the attributes_map, existing information, "
            "and your own best assessment of the product. You are to choose the 3 best attributes available to represent "
            "the item. You will be given any existing information and must strongly consider it for inclusion in the "
            "output you create. The output should be a JSON object with the keys: AttributeOneName, AttributeOneDesc, "
            "AttributeTwoName, AttributeTwoDesc, AttributeThreeName, AttributeThreeDesc."
            "\n Your response should be only the JSON object, and no additional text."
            "\n Example JSON format:"
            "{\n"
            "  \"AttributeOneName\": \"Color\",\n"
            "  \"AttributeOneDesc\": \"Blue\",\n"
            "  \"AttributeTwoName\": \"Size\",\n"
            "  \"AttributeTwoDesc\": \"Medium\",\n"
            "  \"AttributeThreeName\": \"Material\",\n"
            "  \"AttributeThreeDesc\": \"Cotton\"\n"
            "}"
            f"\n Existing product data: {productAttributes}"
            f"\n Existing parent product data: {{'AttributeOneName': '{parentAttributeOneName}', 'AttributeOneDesc': '{parentAttributeOneDesc}', "
            f"'AttributeTwoName': '{parentAttributeTwoName}', 'AttributeTwoDesc': '{parentAttributeTwoDesc}', "
            f"'AttributeThreeName': '{parentAttributeThreeName}', 'AttributeThreeDesc': '{parentAttributeThreeDesc}'}}."
            f"\n Attributes Map: {attributes_map}"
        )

        logging.info("Setting Parent and Child Product responses.")
        print("Setting Parent and Child Product responses.")

        # Call getChatCompletions function to get AI-generated attributes
        resultProductAttributes = getChatCompletions(
            openai_api_key, xxx, productSKU, parent_sku, responseParentProduct, responseChildProduct, thread_id, m_assistant_id, client
        )

        if not resultProductAttributes:
            raise ValueError("AI response is empty")

        # Log the AI response
        logging.info(f"AI Response for Attributes: {resultProductAttributes}")
        print(f"AI Response for Attributes: {resultProductAttributes}")

        # Parse the AI response (extract JSON)
        try:
            json_pattern = re.compile(r'\{.*\}', re.DOTALL)
            # Use regular expression to find the JSON object in the response
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
        logging.info(f"Successfully generated attributes for product at {currentDateTime}")
        print(f"Successfully generated attributes for product at {currentDateTime}")

        # Update the attributes_map with new attributes
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
                    
        # Log and return
        logging.info(f"Processed Product Attributes: {productAttributes}")
        return productAttributes
        
    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Failed to generate attributes for product at {currentDateTime}: {str(e)}")
        print(f"Failed to generate attributes for product at {currentDateTime}: {str(e)}")           
                        
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

# Function to find the parent/variable SKU by checking current product Type for variable status, then checking Parent row
def find_parent_sku(productType, productSKU, prodf, current_index, productParent):
    try:
        with logging_lock:
            logging.info("\n def find_parent_sku: Finding Parent SKU...")
        print("\n def find_parent_sku: Finding Parent SKU...")

        # Case when product is a variable type
        if productType == 'variable':
            print(f"Product is type '{productType}', so Parent SKU is set to: {productSKU}")
            with logging_lock:
                logging.info(f"Product is type '{productType}', so Parent SKU is set to: {productSKU}")
            return productSKU

        # Case when product is not a variable type
        else:
            # Check if productParent is provided, otherwise handle missing/none
            if productParent:
                print(f"Product is not a variable, setting Parent SKU to: {productParent}")
                with logging_lock:
                    logging.info(f"Product is not a variable, setting Parent SKU to: {productParent}")
                return productParent
            else:
                # Log if productParent is missing or not set correctly
                print(f"Warning: Parent SKU for product {productSKU} could not be determined (productParent is None or missing).")
                with logging_lock:
                    logging.error(f"Parent SKU for product {productSKU} could not be determined (productParent is None or missing).")
                return None  

    except Exception as e:
        with logging_lock:
            logging.error(f"Error finding parent SKU for product {productSKU}: {str(e)}")
        print(f"Error finding parent SKU for product {productSKU}: {str(e)}")
        raise                   

# Function to find all sibling/children/variant SKUs by reading forward from the Parent/variable in productlistings.csv to the next parent/variable
def get_children_skus(parent_sku, prodf):
    try:
        with logging_lock:
            logging.info(f"\n def get_children_skus: Finding Children SKUs for Parent SKU: {parent_sku}...")
        print(f"\n def get_children_skus: Finding Children SKUs for Parent SKU: {parent_sku}...")

        children_skus = []

        # List all productSKUs that match the current parent_sku (children_skus)
        with prodf_lock:
            for i in range(len(prodf)):
                # Ensure the SKU and Parent columns are not NaN
                sku = prodf.iloc[i, 2]  # Assuming column 2 is the SKU column
                parent_column = prodf.iloc[i, 32]  # Assuming column 32 is the parent SKU column
                
                # Check if both the SKU and parent_column are not NaN and match the parent_sku
                if pd.notna(sku) and pd.notna(parent_column) and parent_column == parent_sku:
                    children_skus.append(sku)
                    print(f"Child SKU {sku} found at index {i}")
                    with logging_lock:
                        logging.info(f"Child SKU {sku} found at index {i}")
        
        # Log the children SKUs obtained
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.info(f"Successfully obtained Children_SKUs {children_skus} for Parent SKU {parent_sku} at {currentDateTime}") 
        print(f"Successfully obtained Children_SKUs {children_skus} for Parent SKU {parent_sku} at {currentDateTime}")
                    
        return children_skus

    except Exception as e:
        currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with logging_lock:
            logging.error(f"Failed to obtain Children_SKUs for Parent SKU {parent_sku} at {currentDateTime}: {str(e)}")
        print(f"Failed to obtain Children_SKUs for Parent SKU {parent_sku} at {currentDateTime}: {str(e)}")
        raise

def update_productlisting_values(prodf):
    try:
        # Change the following columns to "1" regardless of current value
        prodf['productFeatured'] = 1
        prodf['productFeedback'] = 1
        prodf['productPublished'] = 1
        
        print("Successfully updated productFeatured, productFeedback, and productPublished to '1'")
        
    except KeyError as e:
        print(f"Column {str(e)} does not exist in the dataframe.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

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
    client = initialize_client(openai_api_key)

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
                productParent = row['Parent']
                productUpsell = row['Upsells']
                productCross = row['Cross-sells']
                productAttributeOneName = row['Attribute 1 name']
                productAttributeOneDesc = row['Attribute 1 value(s)']
                productAttributeTwoName = row['Attribute 2 name']
                productAttributeTwoDesc = row['Attribute 2 value(s)']
                productAttributeThreeName = row['Attribute 3 name']
                productAttributeThreeDesc = row['Attribute 3 value(s)']
                productFeatured = row['Is featured?']
                productFeedback = row['Allow customer reviews?']
                productPublished = row['Published']
                
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
                        parent_sku = find_parent_sku(row['Type'], row['SKU'], prodf, current_index, productParent)
                    except Exception as e:
                        with logging_lock:
                            logging.error(f"\n Failed to obtain Parent_SKU at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}: {e}")
                        print(f"\n Failed to obtain Parent_SKU at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}: {e}")
                        continue

                    # Find the parent_sku in the prodf DataFrame
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
                                category_list = category_map[category_key]
            
                                # Separate the hierarchical categories and tags
                                hierarchical_categories = []
                                tags = []
                                for category in category_list:
                                    if "For" in category:  # Tags like "For Ferrets" or "For Humans"
                                        tags.append(category)
                                    else:
                                        hierarchical_categories.append(category)

                                # Join hierarchical categories with " > ", but keep tags separate
                                resultProductCategories = " > ".join(hierarchical_categories) + ", " + ", ".join(tags)
                                resultProductCategories = sanitize_description(resultProductCategories)

                                currentDateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                logging.info(f"\n Matched product '{productName}' with category '{resultProductCategories}' using key '{category_key}' at {currentDateTime}")
                                print(f"\n Matched product '{productName}' with category '{resultProductCategories}' using key '{category_key}' at {currentDateTime}")

                            else:
                                # 3. If no matching category is found in the map, generate categories using getChatCompletions
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
                    # Handle NaN values for productCategories
                    if pd.isna(productTags):
                        productTags = '' 
                    
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
                    resultProductAttributes = generate_product_attributes(openai_api_key, productSKU, parent_sku, thread_id, m_assistant_id, client, prodf, count, productlisting_file_path, attributes_map, logging)
                    












                        
                        
                    # Get productHeight 
                    resultProductHeight = find_or_confirm_height(openai_api_key, productHeight, productName, productSKU, parent_sku, thread_id, m_assistant_id, client)
                    updatedataframe(prodf, count, 'Height (cm)', resultProductHeight, productlisting_file_path) 
                    
                    # Get productLength 
                    resultProductLength = find_or_confirm_length(openai_api_key, productLength, productName, productSKU, parent_sku, thread_id, m_assistant_id, client)
                    updatedataframe(prodf, count, 'Length (cm)', resultProductLength, productlisting_file_path) 
                    
                    # Get productWidth
                    resultProductWidth = find_or_confirm_width(openai_api_key, productWidth, productName, productSKU, parent_sku, thread_id, m_assistant_id, client)
                    updatedataframe(prodf, count, 'Width (cm)', resultProductWidth, productlisting_file_path) 

                    # Get productWeight
                    resultProductWeight = find_or_confirm_weight(openai_api_key, productWeight, productName, productSKU, parent_sku, productHeight, productWidth, productLength, thread_id, m_assistant_id, client)
                    updatedataframe(prodf, count, 'Weight (kg)', resultProductWeight, productlisting_file_path)  
                    
                    # Update productFeatured, productFeedback and productPublished to "1"
                    update_productlisting_values(prodf)
                    
                    # Update productPurchaseNote
                    resultPurchaseNote = write_purchase_note(openai_api_key, resultName, resultProductSDescription, resultProductLDescription, productName, productSKU, parent_sku, thread_id, m_assistant_id, client)

                
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
        attributes_map=attributes_map,
        # complementary_map=dookery.complementary_map
        logging=logging,
        logging_lock=logging_lock,
    )
    logging.warning("\n Warming Up: Let's go!!!")
    print("\n Warming Up: Let's go!!!")
