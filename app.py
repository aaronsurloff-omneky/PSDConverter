import logging
import streamlit as st
from psd_tools import PSDImage
from psd_tools.api.layers import Artboard
import os
import tempfile

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def separate_parts(psd_file):
    psd = PSDImage.open(psd_file)
    output_dir = tempfile.mkdtemp()
    layer_info = []  # List to store layer information
    layer_order = 0  # Initialize layer order

    for i, layer in enumerate(psd):
        if layer.is_visible():
            layer_order += 1  # Increment layer order
            if layer.is_group():
                group_info, group_order = extract_parts_from_group(layer, output_dir, layer_order)
                layer_info.extend(group_info)
                layer_order = group_order  # Update layer order after processing group
            else:
                # Get blending mode of the layer
                blending_mode = layer.blend_mode
                if layer.kind == 'type':
                    # Skip exporting type layers
                    text_info = {
                        'name': layer.name,
                        'bbox': layer.bbox,
                        'kind': layer.kind,
                        'text': layer.text,
                        'order': layer_order,  # Add layer order
                        'style_sheet': layer.engine_dict.get('StyleRun', []),                      
                        'font_list': layer.resource_dict.get('FontSet', []),
                        'blend_mode': blending_mode,  # Add blending mode
                        'layer_effects': layer.effects  # Add layer effects
                    }
                    layer_info.append(text_info)
                else:
                    # Export all other layers as PNG
                    img = layer.composite()
                    img.save(os.path.join(output_dir, f'{layer.name}.png'))
                    # Retain metadata for non-type layers
                    x, y, width, height = layer.bbox
                    # Calculate top-left corner coordinates and width-height
                    top_left_x = x
                    top_left_y = y
                    width = width - x
                    height = height - y
                    layer_info.append({
                        'name': layer.name,
                        'x': top_left_x,
                        'y': top_left_y,
                        'width': width,
                        'height': height,
                        'kind': layer.kind,
                        'order': layer_order,
                        'blend_mode': blending_mode  # Add blending mode
                    })

    return output_dir, layer_info, psd.width, psd.height

def extract_parts_from_group(group, output_dir, group_order):
    group_info = []
    for i, layer in enumerate(group):
        if layer.is_visible():
            group_order += 1  # Increment group order
            if layer.is_group():
                subgroup_info, group_order = extract_parts_from_group(layer, output_dir, group_order)
                group_info.extend(subgroup_info)
            else:
                # Get blending mode of the layer
                blending_mode = layer.blend_mode
                if layer.kind == 'type':
                    text_info = {
                        'name': f'{group.name}_part_{i}',
                        'bbox': layer.bbox,
                        'kind': layer.kind,
                        'text': layer.text,
                        'order': group_order,  # Add group order
                        'style_sheet': layer.engine_dict.get('StyleRun', ['RunArray']), 
                        'font_list': layer.resource_dict.get('FontSet', []),
                        'blend_mode': blending_mode,  # Add blending mode
                        'layer_effects': layer.effects  # Add layer effects
                    }
                    group_info.append(text_info)

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{group.name}_part_{i}.png'))

    return group_info, group_order

def get_artboard_info(psd):
    logging.debug("Getting artboard info...")
    artboard_info = []
    try:
        for layer_order, layer in enumerate(psd):
            if isinstance(layer, Artboard):
                artboard_name = layer.name
                artboard_layers = []  # List to store dictionaries and PSD layer objects
                for sub_layer_order, sub_layer in enumerate(layer):
                    top_left_x, top_left_y, bottom_right_x, bottom_right_y = sub_layer.bbox
                    width = bottom_right_x - top_left_x
                    height = bottom_right_y - top_left_y
                    sub_layer_info = {
                        'name': sub_layer.name,
                        'x': top_left_x,
                        'y': top_left_y,
                        'width': width,
                        'height': height,
                        'kind': sub_layer.kind,
                        'order': sub_layer_order,
                        'blend_mode': sub_layer.blend_mode
                    }
                    artboard_layers.append({
                        'info': sub_layer_info,  # Add dictionary containing layer information
                        'layer': sub_layer  # Add PSD layer object
                    })
                artboard_info.append({
                    'name': artboard_name,
                    'layers': artboard_layers,
                    'artboard': layer
                })
                logging.debug(f"Artboard '{artboard_name}' processed with {len(artboard_layers)} layers.")
    except Exception as e:
        logging.exception("Error in get_artboard_info:")
    return artboard_info


def export_sub_layer_as_png(sub_layer, artboard_name, sub_layer_info):
    # Create a temporary directory to store the exported PNG files
    output_dir = tempfile.mkdtemp()

    # Flatten the sub_layer
    sub_layer_flattened = sub_layer.composite()

    # Export the flattened sub_layer as PNG
    output_path = os.path.join(output_dir, f"{artboard_name}_{sub_layer_info['name']}.png")
    sub_layer_flattened.save(output_path)

    # Display the download button for the exported PNG
    st.download_button(
        label=f"Download {artboard_name}_{sub_layer_info['name']}.png",
        data=open(output_path, "rb").read(),
        file_name=f"{sub_layer_info['name']}.png",
        mime="image/png"
    )



def main():
    st.title("PSD Importer Prototype")
    st.caption("This extracts visible layers, converts all non-images to PNG, outputs text, and tells us the location on the canvas for each exported part")

    uploaded_file = st.file_uploader("Upload a PSD file", type=["psd"])

    if uploaded_file is not None:
        # Open the PSD file
        psd = PSDImage.open(uploaded_file)

        # Log the file info
        logging.debug(f"PSD file opened: {psd}")

        # Get artboard info
        artboard_info = get_artboard_info(psd)

        # Log the artboard info
        logging.debug(f"Artboard info: {artboard_info}")
        
        if artboard_info:
            # Artboards exist in the PSD file
            artboard_names = [info['name'] for info in artboard_info]
            selected_artboard = st.selectbox("Select an artboard", artboard_names)
            for info in artboard_info:
                if info['name'] == selected_artboard:
                    st.subheader(f"Artboard: {info['name']}")
                    st.write(f"Canvas Width: {info['artboard'].width}")
                    st.write(f"Canvas Height: {info['artboard'].height}")
                    st.write("")
                    for entry in info['layers']:
                        sub_layer_info = entry['info']  # Dictionary containing layer information
                        sub_layer = entry['layer']  # PSD layer object

                        st.write(f"  Name: {sub_layer_info['name']}")
                        st.write(f"  X: {sub_layer_info['x']}")
                        st.write(f"  Y: {sub_layer_info['y']}")
                        st.write(f"  Width: {sub_layer_info['width']}")
                        st.write(f"  Height: {sub_layer_info['height']}")
                        st.write(f"  Kind: {sub_layer_info['kind']}")
                        st.write(f"  Order: {sub_layer_info['order']}")
                        st.write(f"  Blend Mode: {sub_layer_info['blend_mode']}")
                        st.write("")

                        # Export sub-layer as PNG
                        export_sub_layer_as_png(sub_layer, selected_artboard, sub_layer_info)
        else:
            # Reset file pointer to the beginning of the file
            uploaded_file.seek(0)
            
            # No artboards found in the PSD file
            output_dir, layer_info, canvas_width, canvas_height = separate_parts(uploaded_file)
            st.write("Canvas Width:", canvas_width)
            st.write("Canvas Height:", canvas_height)
            st.write("Separation completed! Download the separated parts:")
            for filename in os.listdir(output_dir):
                st.download_button(
                    label=filename,
                    data=open(os.path.join(output_dir, filename), "rb").read(),
                    file_name=filename,
                    mime="image/png"
                )

            st.write("Layer Information:")
            for layer in layer_info:
                st.write(f"Name: {layer['name']}")
                if 'x' in layer and 'y' in layer and 'width' in layer and 'height' in layer:
                    st.write(f"Top Left Corner (x, y): ({layer['x']}, {layer['y']})")
                    st.write(f"Width: {layer['width']}")
                    st.write(f"Height: {layer['height']}")
                st.write(f"Kind: {layer['kind']}")
                if layer['kind'] == 'type':
                    st.write(f"Text: {layer['text']}")
                    st.write(f"StyleRun: {layer['style_sheet']}")
                    st.write(f"Font List: {layer['font_list']}")
                    st.write(f"Layer Effects: {layer['layer_effects']}")            
                st.write(f"Blending Mode: {layer.get('blend_mode', 'Normal')}")
                st.write(f"Order: {layer['order']}")
                st.write("")

if __name__ == "__main__":
    main()
