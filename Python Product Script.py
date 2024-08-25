"""must pip install requests once"""

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
