from PIL import Image, ExifTags
import os
import sys


def format_file_size(size):
    """Convert file size from bytes to KB or MB."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


def get_exif_data(image):
    """Get EXIF metadata with readable tag names."""
    exif_data = image.getexif()

    if not exif_data:
        return {}

    readable_data = {}

    for tag_id, value in exif_data.items():
        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
        readable_data[tag_name] = value

    return readable_data


def analyze_image(image_path):
    """Analyze an image and display its metadata."""

    try:
        # Open the image
        image = Image.open(image_path)

        # File information
        file_name = os.path.basename(image_path)
        file_size = os.path.getsize(image_path)

        # Image information
        file_format = image.format
        width, height = image.size
        color_mode = image.mode

        # Pixel resolution
        resolution = f"{width} × {height} pixels"

        # DPI information
        dpi = image.info.get("dpi")

        if dpi:
            dpi_info = f"{dpi[0]:.0f} × {dpi[1]:.0f} DPI"
        else:
            dpi_info = "Not available"

        # Print report
        print("================================")
        print("IMAGE METADATA REPORT")
        print("================================")

        print(f"File Name       : {file_name}")
        print(f"File Size       : {format_file_size(file_size)}")
        print(f"File Format     : {file_format}")
        print(f"Width           : {width} pixels")
        print(f"Height          : {height} pixels")
        print(f"Resolution      : {resolution}")
        print(f"DPI             : {dpi_info}")
        print(f"Color Mode      : {color_mode}")

        # EXIF information
        print("\nEXIF Metadata")
        print("-------------------------------")

        exif_data = get_exif_data(image)

        if exif_data:
            for tag, value in exif_data.items():

                # Make some common EXIF fields easier to understand
                if tag == "Make":
                    print(f"Camera Make     : {value}")

                elif tag == "Model":
                    print(f"Camera Model    : {value}")

                elif tag == "DateTime":
                    print(f"Date Taken      : {value}")

                elif tag == "Orientation":
                    print(f"Orientation     : {value}")

                else:
                    print(f"{tag:<16}: {value}")

        else:
            print("No EXIF metadata found.")

    except FileNotFoundError:
        print(f"Error: File not found: {image_path}")

    except (OSError, ValueError):
        print(f"Error: '{image_path}' is not a supported image file.")


def main():
    """Main function of the program."""

    if len(sys.argv) < 2:
        print("================================")
        print("IMAGE ANALYZER")
        print("================================")
        print("Usage:")
        print("python image_analyzer.py <image_path>")
        return

    image_path = sys.argv[1]

    analyze_image(image_path)


if __name__ == "__main__":
    main()