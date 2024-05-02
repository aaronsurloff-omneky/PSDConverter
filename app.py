import os
import tempfile
from psd_tools import PSDImage
import streamlit as st

def separate_parts(psd_file):
    psd = PSDImage.open(psd_file)
    output_dir = tempfile.mkdtemp()
    layer_info = {}  # Dictionary to store layer information grouped by styling attributes
    layer_order = 0  # Initialize layer order

    for i, layer in enumerate(psd):
        if layer.is_visible():
            layer_order += 1  # Increment layer order
            if layer.is_group():
                group_info, group_order = extract_parts_from_group(layer, output_dir, layer_order)
                # Merge group_info into layer_info dictionary
                layer_info.update(group_info)
                layer_order = group_order  # Update layer order after processing group
            else:
                if layer.kind == 'type':
                    # Get the styling attributes for the current text layer
                    style_sheet = layer.engine_dict.get('StyleRun', None)
                    font_list = layer.resource_dict.get('FontSet', [])

                    # Convert the styling attributes to a hashable format (e.g., tuple)
                    style_attributes = tuple(sorted(style_sheet.items()))

                    # Create a key based on styling attributes to group text runs
                    key = (layer.name, style_attributes)

                    # Add the text layer to the corresponding group in the layer_info dictionary
                    if key in layer_info:
                        layer_info[key]['layers'].append({
                            'name': layer.name,
                            'bbox': layer.bbox,
                            'text': layer.text,
                            'order': layer_order
                        })
                    else:
                        layer_info[key] = {
                            'name': layer.name,
                            'style_sheet': style_sheet,
                            'font_list': font_list,
                            'layers': [{
                                'name': layer.name,
                                'bbox': layer.bbox,
                                'text': layer.text,
                                'order': layer_order
                            }]
                        }

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{layer.name}.png'))

    return output_dir, list(layer_info.values()), psd.width, psd.height  # Convert dictionary values to list

def extract_parts_from_group(group, output_dir, group_order):
    group_info = []
    for i, layer in enumerate(group):
        if layer.is_visible():
            group_order += 1  # Increment group order
            if layer.is_group():
                subgroup_info, group_order = extract_parts_from_group(layer, output_dir, group_order)
                group_info.extend(subgroup_info)
            else:
                if layer.kind == 'type':
                    text_info = {
                        'name': f'{group.name}_part_{i}',
                        'bbox': layer.bbox,
                        'kind': layer.kind,
                        'text': layer.text,
                        'order': group_order,  # Add group order
                        'style_sheet': layer.engine_dict.get('StyleRun', None),
                        'font_list': layer.resource_dict.get('FontSet', [])
                    }
                    
                    group_info.append(text_info)

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{group.name}_part_{i}.png'))

    return group_info, group_order

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
        st.write(f"Bounding Box: {layer['bbox']}")
        st.write(f"Kind: {layer['kind']}")
        if layer['kind'] == 'type':
            st.write(f"Text: {layer['text']}")
            st.write(f"StyleRun: {layer['style_sheet']}")
            st.write(f"Font List: {layer['font_list']}")
        st.write(f"Order: {layer['order']}")  # Print layer order
        st.write("")
