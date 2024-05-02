import os
import tempfile
from psd_tools import PSDImage
import streamlit as st

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
                        'style_sheet': layer.engine_dict.get('StyleRun', ['RunArray']),
                        'font_list': layer.resource_dict.get('FontSet', []),
                        'blend_mode': blending_mode  # Add blending mode
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
                        'blend_mode': blending_mode  # Add blending mode
                    }
                    group_info.append(text_info)

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{group.name}_part_{i}.png'))

    return group_info, group_order

# Streamlit UI code
st.title("PSD Importer Prototype")
st.caption("This extracts visible layers, converts all non-images to PNG, outputs text, and tells us the location on the canvas for each exported part")

uploaded_file = st.file_uploader("Upload a PSD file", type=["psd"])

if uploaded_file is not None:
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
        # Print blending mode
        st.write(f"Blending Mode: {layer.get('blend_mode', 'Normal')}")
        st.write(f"Order: {layer['order']}")
        st.write("")
