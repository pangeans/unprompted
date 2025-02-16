import psycopg2
import os

def load_image(image_path, prompt_keywords):
    conn = psycopg2.connect(
        host=os.getenv("NEON_DB_HOST"),
        user=os.getenv("NEON_DB_USER"),
        password=os.getenv("NEON_DB_PASSWORD"),
        dbname=os.getenv("NEON_DB_NAME")
    )
    cursor = conn.cursor()
    with open(image_path, "rb") as image_file:
        binary_image = image_file.read()
        cursor.execute(
            "INSERT INTO images (image, prompt_keywords) VALUES (%s, %s)",
            (binary_image, prompt_keywords)
        )
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    image_path = "path/to/your/image.jpg"
    prompt_keywords = "example, keywords"
    load_image(image_path, prompt_keywords)
