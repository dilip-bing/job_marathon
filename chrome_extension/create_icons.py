"""
Generate placeholder icons for Chrome extension
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a simple gradient icon with size text"""
    # Create image with gradient background
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background (purple to blue)
    for y in range(size):
        r = int(102 + (118 - 102) * y / size)
        g = int(126 + (75 - 126) * y / size)
        b = int(234 + (162 - 234) * y / size)
        draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b))
    
    # Draw a simple robot emoji-like design
    # Head
    head_size = int(size * 0.4)
    head_x = (size - head_size) // 2
    head_y = int(size * 0.3)
    draw.rounded_rectangle(
        [(head_x, head_y), (head_x + head_size, head_y + head_size)],
        radius=int(head_size * 0.1),
        fill='white'
    )
    
    # Eyes
    eye_size = int(head_size * 0.15)
    eye_y = head_y + int(head_size * 0.35)
    left_eye_x = head_x + int(head_size * 0.25)
    right_eye_x = head_x + int(head_size * 0.6)
    
    draw.ellipse(
        [(left_eye_x, eye_y), (left_eye_x + eye_size, eye_y + eye_size)],
        fill=(102, 126, 234)
    )
    draw.ellipse(
        [(right_eye_x, eye_y), (right_eye_x + eye_size, eye_y + eye_size)],
        fill=(102, 126, 234)
    )
    
    # Smile
    mouth_y = head_y + int(head_size * 0.6)
    mouth_width = int(head_size * 0.5)
    mouth_x = head_x + int(head_size * 0.25)
    draw.arc(
        [(mouth_x, mouth_y), (mouth_x + mouth_width, mouth_y + int(head_size * 0.2))],
        start=0, end=180,
        fill=(102, 126, 234),
        width=2
    )
    
    # Save
    img.save(output_path, 'PNG')
    print(f'Created {output_path}')

def main():
    # Create icons directory if it doesn't exist
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    # Generate icons
    sizes = [16, 48, 128]
    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon{size}.png')
        create_icon(size, output_path)
    
    print('\n✅ All icons created successfully!')

if __name__ == '__main__':
    main()
