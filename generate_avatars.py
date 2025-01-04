from PIL import Image, ImageDraw
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
    
    # Get absolute path for the output directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, 'app', 'static', 'images', 'default-avatars')
    
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        print(f'Output directory: {output_dir}')
        
        # Size for avatars
        size = (400, 400)
        
        for i, color in enumerate(colors, 1):
            try:
                # Create new image with given color
                img = Image.new('RGB', size, color)
                draw = ImageDraw.Draw(img)
                
                # Add a subtle pattern
                for y in range(0, size[1], 4):
                    draw.line([(0, y), (size[0], y)], fill=adjust_brightness(color, -10), width=2)
                
                # Add a circle in the center
                circle_radius = size[0] // 4
                circle_center = (size[0] // 2, size[1] // 2)
                circle_bbox = (
                    circle_center[0] - circle_radius,
                    circle_center[1] - circle_radius,
                    circle_center[0] + circle_radius,
                    circle_center[1] + circle_radius
                )
                draw.ellipse(circle_bbox, fill=adjust_brightness(color, 20))
                
                # Save the avatar
                output_path = os.path.join(output_dir, f'avatar{i}.png')
                img.save(output_path, 'PNG', quality=95)
                print(f'Generated avatar{i}.png at {output_path}')
                
            except Exception as e:
                print(f'Error generating avatar{i}.png: {str(e)}')
                
    except Exception as e:
        print(f'Error creating output directory: {str(e)}')

def adjust_brightness(hex_color, factor):
    """Adjust the brightness of a hex color"""
    try:
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Adjust brightness
        r = max(0, min(255, r + factor))
        g = max(0, min(255, g + factor))
        b = max(0, min(255, b + factor))
        
        return f'#{r:02x}{g:02x}{b:02x}'
    except Exception as e:
        print(f'Error adjusting brightness: {str(e)}')
        return hex_color

if __name__ == '__main__':
    print('Generating default avatars...')
    generate_default_avatars()
    print('Done!') 