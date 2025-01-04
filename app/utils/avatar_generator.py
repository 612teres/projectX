from PIL import Image, ImageDraw, ImageFont
import os

def generate_default_avatars():
    """Generate a set of default avatars with different colors and styles"""
    
    # Colors for avatars (background colors)
    colors = [
        '#4F46E5',  # Indigo
        '#10B981',  # Emerald
        '#F59E0B',  # Amber
        '#EF4444',  # Red
        '#8B5CF6',  # Purple
        '#EC4899',  # Pink
        '#06B6D4',  # Cyan
        '#84CC16',  # Lime
        '#3B82F6',  # Blue
        '#F97316',  # Orange
        '#6366F1',  # Violet
        '#14B8A6',  # Teal
    ]
    
    # Ensure the default avatars directory exists
    output_dir = os.path.join('app', 'static', 'images', 'default-avatars')
    os.makedirs(output_dir, exist_ok=True)
    
    # Size for avatars
    size = (400, 400)
    
    for i, color in enumerate(colors, 1):
        # Create new image with given color
        img = Image.new('RGB', size, color)
        draw = ImageDraw.Draw(img)
        
        # Add a subtle pattern or gradient
        for y in range(0, size[1], 4):
            draw.line([(0, y), (size[0], y)], fill=adjust_brightness(color, -10), width=2)
        
        # Save the avatar
        output_path = os.path.join(output_dir, f'avatar{i}.png')
        img.save(output_path, 'PNG', quality=95)

def adjust_brightness(hex_color, factor):
    """Adjust the brightness of a hex color"""
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Adjust brightness
    r = max(0, min(255, r + factor))
    g = max(0, min(255, g + factor))
    b = max(0, min(255, b + factor))
    
    return f'#{r:02x}{g:02x}{b:02x}'

if __name__ == '__main__':
    generate_default_avatars() 