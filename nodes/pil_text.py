#---------------------------------------------------------------------------------------------------------------------#
# Comfyroll Custom Nodes by RockOfFire and Akatsuzi     https://github.com/RockOfFire/ComfyUI_Comfyroll_CustomNodes                             
# for ComfyUI                                           https://github.com/comfyanonymous/ComfyUI                                               
#---------------------------------------------------------------------------------------------------------------------#

import numpy as np
import torch
import os 
from PIL import Image, ImageDraw, ImageOps, ImageFont
from ..categories import icons
from ..config import color_mapping, COLORS
from .graphics_functions import (draw_masked_text,
                                 hex_to_rgb,
                                 draw_text_on_image,
                                 get_font_size,
                                 get_text_size,
                                 get_color_values,
                                 reduce_opacity)

'''
try:
    from bidi.algorithm import get_display
except ImportError:
    import subprocess
    subprocess.check_call(['python', '-m', 'pip', 'install', 'python_bidi'])

try:    
    import arabic_reshaper    
except ImportError:
    import subprocess
    subprocess.check_call(['python', '-m', 'pip', 'install', 'arabic_reshaper'])
'''

font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "fonts")       
file_list = [f for f in os.listdir(font_dir) if os.path.isfile(os.path.join(font_dir, f)) and f.lower().endswith(".ttf")]

#---------------------------------------------------------------------------------------------------------------------#
          
ALIGN_OPTIONS = ["top", "center", "bottom"]                 
ROTATE_OPTIONS = ["text center", "image center"]
JUSTIFY_OPTIONS = ["left", "center", "right"]
PERSPECTIVE_OPTIONS = ["top", "bottom", "left", "right"]

#---------------------------------------------------------------------------------------------------------------------#

def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0) 
    
#---------------------------------------------------------------------------------------------------------------------#
class CR_OverlayText:

    @classmethod
    def INPUT_TYPES(s):
                        
        return {"required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "text"}),
                "font_name": (file_list,),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024}),
                "font_color": (COLORS,), 
                "align": (ALIGN_OPTIONS,),
                "justify": (JUSTIFY_OPTIONS,),
                "margins": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "line_spacing": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "position_x": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "position_y": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "rotation_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1}),
                "rotation_options": (ROTATE_OPTIONS,),
                },
                "optional": {"font_color_hex": ("STRING", {"multiline": False, "default": "#000000"})
                }        
    }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "overlay_text"
    CATEGORY = icons.get("Comfyroll/Graphics/Text")

    def overlay_text(self, image, text, font_name, font_size, font_color,  
                     margins, line_spacing,
                     position_x, position_y,
                     align, justify,
                     rotation_angle, rotation_options,
                     font_color_hex='#000000'):

        # Get RGB values for the text color  
        text_color = get_color_values(font_color, font_color_hex, color_mapping)
      
        # Convert tensor images
        image_3d = image[0, :, :, :]

        # Create PIL images for the text and background layers and text mask
        back_image = tensor2pil(image_3d)
        text_image = Image.new('RGB', back_image.size, text_color)
        text_mask = Image.new('L', back_image.size)
        
        # Draw the text on the text mask
        rotated_text_mask = draw_masked_text(text_mask, text, font_name, font_size,
                                             margins, line_spacing, 
                                             position_x, position_y,
                                             align, justify,
                                             rotation_angle, rotation_options)

        # Composite the text image onto the background image using the rotated text mask       
        image_out = Image.composite(text_image, back_image, rotated_text_mask)       
        
        # Convert the PIL image back to a torch tensor
        return pil2tensor(image_out), 

#---------------------------------------------------------------------------------------------------------------------#
class CR_DrawText:

    @classmethod
    def INPUT_TYPES(s):
                        
        return {"required": {
                "image_width": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "image_height": ("INT", {"default": 512, "min": 64, "max": 2048}),  
                "text": ("STRING", {"multiline": True, "default": "text"}),
                "font_name": (file_list,),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024}),
                "font_color": (COLORS,),
                "background_color": (COLORS,),
                "align": (ALIGN_OPTIONS,),
                "justify": (JUSTIFY_OPTIONS,),
                "margins": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "line_spacing": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "position_x": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "position_y": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "rotation_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1}),
                "rotation_options": (ROTATE_OPTIONS,),            
                },
                "optional": {
                "font_color_hex": ("STRING", {"multiline": False, "default": "#000000"}),
                "bg_color_hex": ("STRING", {"multiline": False, "default": "#000000"})
                }          
    }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "draw_text"
    CATEGORY = icons.get("Comfyroll/Graphics/Text")

    def draw_text(self, image_width, image_height, text,
                  font_name, font_size, font_color, background_color,
                  margins, line_spacing,
                  position_x, position_y,
                  align, justify,
                  rotation_angle, rotation_options,
                  font_color_hex='#000000', bg_color_hex='#000000'):

        # Get RGB values for the text and background colors
        text_color = get_color_values(font_color, font_color_hex, color_mapping)
        bg_color = get_color_values(background_color, bg_color_hex, color_mapping) 
        
        # Create PIL images for the text and background layers and text mask
        size = (image_width, image_height)
        text_image = Image.new('RGB', size, text_color)
        back_image = Image.new('RGB', size, bg_color)
        text_mask = Image.new('L', back_image.size)

        # Draw the text on the text mask
        rotated_text_mask = draw_masked_text(text_mask, text, font_name, font_size,
                                             margins, line_spacing,
                                             position_x, position_y,
                                             align, justify,
                                             rotation_angle, rotation_options)

        # Composite the text image onto the background image using the rotated text mask
        image_out = Image.composite(text_image, back_image, rotated_text_mask)
        
        # Convert the PIL image back to a torch tensor
        return pil2tensor(image_out), 
    
#---------------------------------------------------------------------------------------------------------------------#
class CR_MaskText:

    @classmethod
    def INPUT_TYPES(s):
                      
        return {"required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "text"}),
                "font_name": (file_list,),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024}),
                "background_color": (COLORS,),
                "align": (ALIGN_OPTIONS,),
                "justify": (JUSTIFY_OPTIONS,),
                "margins": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "line_spacing": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "position_x": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "position_y": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "rotation_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1}),
                "rotation_options": (ROTATE_OPTIONS,),             
                },
                "optional": {
                "bg_color_hex": ("STRING", {"multiline": False, "default": "#000000"})
                }         
    }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "mask_text"
    CATEGORY = icons.get("Comfyroll/Graphics/Text")
    
    def mask_text(self, image, text, font_name, font_size,
                  margins, line_spacing, 
                  position_x, position_y, background_color, 
                  align, justify,
                  rotation_angle, rotation_options,
                  bg_color_hex='#000000'):

        # Get RGB values for the background color
        bg_color = get_color_values(background_color, bg_color_hex, color_mapping)   
   
        # Convert tensor images
        image_3d = image[0, :, :, :]
            
        # Create PIL images for the text and background layers and text mask
        text_image = tensor2pil(image_3d)        
        text_mask = Image.new('L', text_image.size)
        background_image = Image.new('RGB', text_mask.size, bg_color)        

        # Draw the text on the text mask
        rotated_text_mask = draw_masked_text(text_mask, text, font_name, font_size,
                                             margins, line_spacing,
                                             position_x, position_y,
                                             align, justify,
                                             rotation_angle, rotation_options)

        # Invert the text mask (so the text is white and the background is black)
        text_mask = ImageOps.invert(rotated_text_mask)        

        # Composite the text image onto the background image using the inverted text mask        
        image_out = Image.composite(background_image, text_image, text_mask)
        
        # Convert the PIL image back to a torch tensor
        return pil2tensor(image_out),

#---------------------------------------------------------------------------------------------------------------------#
class CR_CompositeText:

    @classmethod
    def INPUT_TYPES(s):
                             
        return {"required": {
                "image_text": ("IMAGE",),
                "image_background": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "text"}),
                "font_name": (file_list,),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024}),
                "align": (ALIGN_OPTIONS,),
                "justify": (JUSTIFY_OPTIONS,),
                "margins": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "line_spacing": ("INT", {"default": 0, "min": -1024, "max": 1024}),
                "position_x": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "position_y": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "rotation_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1}),
                "rotation_options": (ROTATE_OPTIONS,),
                }        
    }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "composite_text"
    CATEGORY = icons.get("Comfyroll/Graphics/Text")
    
    def composite_text(self, image_text, image_background, text,
                       font_name, font_size, 
                       margins, line_spacing,
                       position_x, position_y,
                       align, justify,
                       rotation_angle, rotation_options):

        # Convert tensor images
        image_text_3d = image_text[0, :, :, :]
        image_back_3d = image_background[0, :, :, :]
            
        # Create PIL images for the text and background layers and text mask
        text_image = tensor2pil(image_text_3d)
        back_image = tensor2pil(image_back_3d)
        text_mask = Image.new('L', back_image.size)

        # Draw the text on the text mask
        rotated_text_mask = draw_masked_text(text_mask, text, font_name, font_size,
                                             margins, line_spacing,
                                             position_x, position_y,
                                             align, justify,
                                             rotation_angle, rotation_options)
                                             
        # Composite the text image onto the background image using the rotated text mask
        image_out = Image.composite(text_image, back_image, rotated_text_mask)
        
        # Convert the PIL image back to a torch tensor
        return pil2tensor(image_out),

#---------------------------------------------------------------------------------------------------------------------#
class CR_ArabicTextRTL:
    
    @classmethod
    def INPUT_TYPES(s):
                        
        return {"required": {
                "arabic_text": ("STRING", {"multiline": True, "default": "شمس"}),
                }          
        }

    RETURN_TYPES = ("STRING", "STRING", )
    RETURN_NAMES = ("arabic_text_rtl", "show help", )
    FUNCTION = "adjust_arabic_to_rtl"
    CATEGORY = icons.get("Comfyroll/Graphics/Text")

    def adjust_arabic_to_rtl(self, arabic_text):
        """
        Adjust Arabic text to read from right to left (RTL).
        
        Args:
            arabic_text (str): The Arabic text to be adjusted.
            
        Returns:
            str: The adjusted Arabic text in RTL format.
        """
        
        arabic_text_reshaped = arabic_reshaper.reshape(arabic_text)
        rtl_text = get_display(arabic_text_reshaped)
        
        show_help = "example help text"
                
        return rtl_text, show_help,

#---------------------------------------------------------------------------------------------------------------------#
class CR_SimpleTextWatermark:
    
    @classmethod
    def INPUT_TYPES(s):
    
        ALIGN_OPTIONS = ["center", "top left", "top right", "bottom left", "bottom right"]  
                   
        return {"required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": False, "default": "@ your name"}),
                "align": (ALIGN_OPTIONS,),
                "opacity": ("FLOAT", {"default": 0.10, "min": 0.00, "max": 1.00, "step": 0.01}),
                "font_name": (file_list,),
                "font_size": ("INT", {"default": 30, "min": 1, "max": 1024}),                
                "font_color": (COLORS[1:],), 
                "margins": ("INT", {"default": 10, "min": -1024, "max": 1024}),
                }     
        }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "overlay_text"
    CATEGORY = icons.get("Comfyroll/Graphics/Text")

    def overlay_text(self, image, text, align, font_name, font_size, font_color, opacity, margins):
        
        # Create PIL images for the background layer
        image = tensor2pil(image)
        
        textlayer = Image.new("RGBA", image.size)
        draw = ImageDraw.Draw(textlayer)
        
        # Load the font
        font_file = "fonts\\" + str(font_name)   
        resolved_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), font_file)
        font = ImageFont.truetype(str(resolved_font_path), size=font_size)
        
        # Get the size of the text
        textsize = get_text_size(draw, text, font)
        
        # Calculate the position to place the text based on the alignment
        if align == 'center':
            textpos = [(image.size[0] - textsize[0]) // 2, (image.size[1] - textsize[1]) // 2]
        elif align == 'top left':
            textpos = [margins, margins]
        elif align == 'top right':
            textpos = [image.size[0] - textsize[0] - margins, margins]
        elif align == 'bottom left':
            textpos = [margins, image.size[1] - textsize[1] - margins]
        elif align == 'bottom right':
            textpos = [image.size[0] - textsize[0] - margins, image.size[1] - textsize[1] - margins]
        
        # Draw the text on the text layer
        draw.text(textpos, text, font=font, fill=font_color)
        
        # Adjust the opacity of the text layer if needed
        if opacity != 1:
            textlayer = reduce_opacity(textlayer, opacity)
        
        # Composite the text layer on top of the original image
        image_out = Image.composite(textlayer, image, textlayer)
        
        # Convert the PIL image back to a torch tensor
        return pil2tensor(image_out), 

#---------------------------------------------------------------------------------------------------------------------#
# MAPPINGS
#---------------------------------------------------------------------------------------------------------------------#
# For reference only, actual mappings are in __init__.py
'''
NODE_CLASS_MAPPINGS = {
    "CR Overlay Text":CR_OverlayText,
    "CR Draw Text":CR_DrawText, 
    "CR Mask Text":CR_MaskText,
    "CR Composite Text":CR_CompositeText,
    "CR Draw Perspective Text":CR_DrawPerspectiveText,
    "CR Arabic Text RTL": CR_ArabicTextRTL,
    "CR Simple Text Watermark": CR_SimpleTextWatermark,
}
'''

