import cv2
from backend.processing import extract_picture_bg_2024, read_mrz_bg_2024

def test_extract_picture_bg_2024(image_path):
    # Read the image from the file
    card_front = cv2.imread(image_path)
    
    # Check if the image was successfully loaded
    if card_front is None:
        print(f"Failed to load image from {image_path}")
        return
    
    # Call the function with the loaded image
    result = extract_picture_bg_2024(card_front)
    
    # Print the shape of the result to verify the output
    print("Original shape:", card_front.shape)
    print("Extracted shape:", result.shape)
    
    # Display the original and extracted images
    cv2.imshow("Original Image", card_front)
    cv2.imshow("Extracted Image", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test_read_mrz_bg_2024(image_path):
    card_back = cv2.imread(image_path)

    if card_back is None:
        print(f"Failed to load image from {image_path}")
        return
    
    result = read_mrz_bg_2024(card_back)
    print(result)

if __name__ == "__main__":
    # Replace 'path/to/your/image.jpg' with the actual path to your image file
    test_extract_picture_bg_2024('New_Bulgarian_ID_card_(front).png')

    test_read_mrz_bg_2024("Bulgarian_Identity_card_-_back_(2024).png")