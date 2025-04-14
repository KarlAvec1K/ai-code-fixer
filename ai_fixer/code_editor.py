def overwrite_file(filepath, new_content):
    with open(filepath, "w") as f:
        f.write(new_content)
    print(f"✅ Fichier modifié : {filepath}")
