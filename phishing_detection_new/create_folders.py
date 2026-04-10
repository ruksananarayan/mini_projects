import os

def create_folders():
    folders = [
        'static/css',
        'static/js', 
        'static/images',
        'templates'
    ]
    
    print("Creating folder structure...")
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Created: {folder}")
        except Exception as e:
            print(f"❌ Error creating {folder}: {e}")
    
    print("\n📁 Folder structure created successfully!")
    print("phishing_detection/")
    print("├── static/")
    print("│   ├── css/")
    print("│   ├── js/")
    print("│   └── images/")
    print("└── templates/")

if __name__ == "__main__":
    create_folders()