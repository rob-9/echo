import os
import requests
from PIL import Image
from io import BytesIO

# Create the services directory if it doesn't exist
os.makedirs('static/images/services', exist_ok=True)

# List of image URLs and their corresponding filenames
images = {
    'logo-design.jpg': 'https://images.unsplash.com/photo-1626785774573-4b799315345d?w=800&q=80',
    'social-media.jpg': 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&q=80',
    'print-design.jpg': 'https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?w=800&q=80',
    '3d-product.jpg': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80',
    'arch-viz.jpg': 'https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=800&q=80',
    'character-design.jpg': 'https://images.unsplash.com/photo-1618005198919-d3d4b5a92ead?w=800&q=80',
    'web-design.jpg': 'https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&q=80',
    'mobile-ui.jpg': 'https://images.unsplash.com/photo-1551650975-87deedd944c3?w=800&q=80',
    'dashboard.jpg': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80',
    'digital-art.jpg': 'https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=800&q=80',
    'character-illustration.jpg': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80',
    'infographic.jpg': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80',
    '2d-animation.jpg': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80',
    'motion-graphics.jpg': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80',
    '3d-animation.jpg': 'https://images.unsplash.com/photo-1618005198919-d3d4b5a92ead?w=800&q=80'
}

def download_and_resize_image(url, filename, size=(800, 600)):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Open the image and resize it
        img = Image.open(BytesIO(response.content))
        img = img.convert('RGB')  # Convert to RGB if needed
        img = img.resize(size, Image.Resampling.LANCZOS)
        
        # Save the resized image
        img.save(f'static/images/services/{filename}', 'JPEG', quality=85)
        print(f'Successfully downloaded and resized {filename}')
    except Exception as e:
        print(f'Error processing {filename}: {str(e)}')

def main():
    for filename, url in images.items():
        download_and_resize_image(url, filename)

if __name__ == '__main__':
    main() 