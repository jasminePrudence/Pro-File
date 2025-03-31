import chardet
import fitz
from flask import Flask, flash, render_template, request, send_file,  redirect, url_for, session
import pandas as pd
import os
from werkzeug.utils import secure_filename
import re
from flask_mail import Mail, Message
from dotenv import load_dotenv
import io
import pymupdf
import PIL
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# from pdfminer.high_level import extract_text

#Crée une instance de Flask
app = Flask(__name__)
app.secret_key = "secretkey"  # Nécessaire pour utiliser `session`

#Définit les dossiers où stocker les fichiers envoyés et nettoyés
UPLOAD_FOLDER = "upload_data"
OUTPUT_FOLDER = "outputs_data"
FORMATTED_FOLDER = "formatted_data"
FORMATTED_MIN_FOLDER = "formatted_min_data"
REMOVED_NULL_FOLDER = "removed_null_data"
REMOVED_DUPLICATE_FOLDER = "removed_duplicate_data"
CLEANED_COLUMN_FOLDER = "cleaned_column_data"
CLEANED_FOLDER = "cleaned_data"
ALLOWED_EXTENSIONS = {'csv', 'pdf'}
CHANGED_ENCODING_FOLDER = "changed_encoding_data"
REMOVED_SPECIAL_CHARACTERS_FOLDER= "cleaned_special_characters_data"
CONVERTED_EXCEL = "converted_excel_data"
CONVERTED_JSON = "converted_json_data"
COMPRESSED_CSV = "compressed_csv_data"
COMPRESSED_FOLDER = "compressed_data"
CONCATENED_FOLDER = "concatened_data"
CONVERTED_PARQUET = "converted_parquet_data"
ADDED_PDF = "added_pdf_data"
EXTRACTED_TEXT_PDF = "extracted_text_pdf_data"
EXTRACTED_IMAGE_PDF = "extracted_image_pdf_data"
EXTRACTED_METADATA_PDF = "extracted_metadata_pdf_data"
STATIC_FOLDER = os.path.join(os.getcwd(), 'static')



#Crée ces dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, FORMATTED_FOLDER, ADDED_PDF, FORMATTED_MIN_FOLDER, REMOVED_NULL_FOLDER, REMOVED_DUPLICATE_FOLDER,
               CLEANED_COLUMN_FOLDER, CLEANED_FOLDER, CHANGED_ENCODING_FOLDER, REMOVED_SPECIAL_CHARACTERS_FOLDER, COMPRESSED_FOLDER, 
               CONVERTED_EXCEL, CONVERTED_JSON, COMPRESSED_CSV, CONCATENED_FOLDER, CONVERTED_PARQUET, EXTRACTED_IMAGE_PDF, EXTRACTED_METADATA_PDF,
               EXTRACTED_TEXT_PDF, STATIC_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/github')
def github():
    return redirect("https://github.com/jasminePrudence/Pro-File.git")

@app.route('/traitement_csv')
def treatment():
    return render_template('traitement_csv.html')

            
@app.route('/traitement_pdf')
def convert():
    return render_template('traitement_pdf.html')    
            

def save_file(folder, filename, file):
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    return filepath 

# Détection automatique du séparateur
def detect_separator(file_path, encoding):
    with open(file_path, "r", encoding=encoding) as f:
        first_line = f.readline()
        separators = [",", ";", "\t", "|"]
        for sep in separators:
            if sep in first_line:
                return sep
    return ","  # Par défaut, utiliser la virgule

#Formatage des données
def format_names(df):
    nom = next((col for col in df.columns if "nom" in col.lower() or "last" in col.lower()), None)
    prenom = next((col for col in df.columns if "prénom" in col.lower() or "first" in col.lower()), None)
    if not nom or not prenom:
        raise KeyError("Les colonnes contenant 'Nom' ou 'Prénom' doivent être présentes dans le fichier.")
    df[nom] = df[nom].apply(lambda x: str(x).upper() if pd.notna(x) else x)
    df[prenom] = df[prenom].apply(lambda x: str(x).capitalize() if pd.notna(x) else x)

    # Trier les données par ordre alphabétique selon "Nom" puis "Prénom"
    df = df.sort_values(by=[nom, prenom], ascending=[True, True]).reset_index(drop=True)
    return df

def format_min_names(df):
    nom = next((col for col in df.columns if "nom" in col.lower()), None)
    if not nom :
        raise KeyError("Les colonnes contenant 'nom' doivent être présentes dans le fichier.")
    else :
        df[nom] = df[nom].apply(lambda x: str(x).lower() if pd.notna(x) else x)
        df = df.sort_values(by=[nom], ascending=[True]).reset_index(drop=True)

        return df

# Fonction pour supprimer les valeurs nulles
def remove_nulls(df):
    return df.fillna("Inconnu")

# Fonction pour supprimer les doublons
def remove_duplicates(df):
    return df.drop_duplicates()

# Fonction pour nettoyer les noms de colonnes
def clean_column_names(df):
    df.columns = [col.strip().upper().replace(' ', '_') for col in df.columns]
    return df

# Fonction pour supprimer les caractères spéciaux
def remove_special_characters(df):
    df = df.applymap(lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', str(x)) if isinstance(x, str) else x)
    return df

#Nettoyage des données (clean_data)
def apply_all_transformations(df):
    df = remove_nulls(df)
    df = remove_duplicates(df)
    df = clean_column_names(df)
    df = remove_special_characters(df)
    return df

# Fonction pour vérifier si le fichier est un CSV
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Détecter l'encodage du fichier CSV
def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)
    result = raw_data
    result = chardet.detect(raw_data)
    encoding = result["encoding"]
    return encoding

#Convertir CSV en Excel
def convert_excel(df):
    output_path = os.path.join(CONVERTED_EXCEL, "resultat.xlsx")
    df.to_excel(output_path, index=False)
    return output_path  # Retourner le chemin du fichier créé

#Convertir CSV en JSON
def convert_json(df):
    output_path = os.path.join(CONVERTED_JSON, "resultat.json")
    df.to_json(output_path, orient="records")
    return output_path  # 🔹 Retourner le chemin du fichier au lieu du DataFrame

#Convertir CSV en JSON
def convert_parquet(df):
    output_path = os.path.join(CONVERTED_PARQUET, "resultat.parquet")
    df.to_parquet(output_path, engine="pyarrow", index=False)  # Conversion en Parquet
    return output_path  # 🔹 Retourner le chemin du fichier au lieu du DataFrame

#Tester si le fichier est bien csv
def is_csv(file_path):
    #Vérifie si le fichier est bien un CSV
    if not file_path.lower().endswith(".csv"):
        return False
    try:
        # Essayer de lire les 5 premières lignes pour confirmer
        pd.read_csv(file_path, nrows=5)
        return True
    except Exception:
        return False  # Si erreur, ce n'est pas un CSV


def format_filename(filename):
    # Supprimer l'extension du fichier
    name, ext = os.path.splitext(filename)  
    # Remplacer les espaces et caractères spéciaux par des underscores
    formatted_name = re.sub(r'[^\w]+', '_', name)
    # Retourner le nom formaté avec l'extension
    return f"{formatted_name}{ext}"


#Fonction de compression csv
def compress_csv_file(input_path):
    #Compresse un fichier CSV en Gzip et retourne les tailles
    if not is_csv(input_path):
        raise ValueError("Le fichier fourni n'est pas un fichier CSV valide.")
    df = pd.read_csv(input_path)
    filename = os.path.basename(input_path) + ".gz"
    compressed_path = os.path.join(COMPRESSED_FOLDER, filename)
    df.to_csv(compressed_path, compression="gzip", index=False)

    # Taille avant et après compression
    orig_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(compressed_path)
    ratio = (compressed_size / orig_size) * 100 if orig_size > 0 else 0
    return compressed_path, filename, orig_size, compressed_size, ratio

@app.route("/compress_csv", methods=["GET", "POST"])
def compress_csv():
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("traitement_csv.html", message="Aucun fichier sélectionné.")
        file = request.files["file"]
        if file.filename == "":
            return render_template("traitement_csv.html", message="Veuillez sélectionner un fichier CSV.")

        # Sauvegarde du fichier uploadé
        filename = secure_filename(file.filename)
        orig_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(orig_path)
        try:
            compressed_path, compressed_filename, orig_size, compressed_size, ratio = compress_csv_file(orig_path)
            # Si le ratio est >= 100%, on ne compresse pas et on affiche un message
            if ratio >= 100:
                return render_template("traitement_csv.html", message="Compression inefficace : Le fichier compressé est plus grand ou égal à l'original.")
            return render_template(
                "result.html",
                filename=compressed_filename,
                orig_size=orig_size,
                compressed_size=compressed_size,
                ratio=f"{ratio:.2f}%",
                compressed_path=compressed_path,
                ratio_class="green"  # Passer la classe dynamique
            )
        except ValueError:
            return render_template("traitement_csv.html", message="Erreur : Le fichier n'est pas un CSV valide.")
    return render_template("traitement_csv.html")

############################################Cette route reçoit un fichier CSV
@app.route('/upload_csv', methods=['POST'])
def upload_csv():   
    if 'file' not in request.files:
        return render_template("traitement_csv.html", message="Aucun fichier sélectionné.")        
    file = request.files['file']
    if file and file.filename.endswith(".csv"):
        filename = secure_filename(file.filename)
        original_filepath = save_file(UPLOAD_FOLDER, filename, file)

        encoding = detect_encoding(original_filepath)
        separator = detect_separator(original_filepath, encoding)
        df_preview = pd.read_csv(original_filepath, sep=separator, encoding=encoding)  # Charger tout le fichier
    # Vérifier quel bouton a été pressé et appliquer la transformation appropriée
    transformations = {
        'format_names': (format_names, FORMATTED_FOLDER, "formatted_"),
        'format_min_names': (format_min_names, FORMATTED_MIN_FOLDER, "formatted_min_"),
        'remove_nulls': (remove_nulls, REMOVED_NULL_FOLDER, "removed_null_"),
        'remove_duplicates': (remove_duplicates, REMOVED_DUPLICATE_FOLDER, "removed_duplicate_"),
        'clean_columns': (clean_column_names, CLEANED_COLUMN_FOLDER, "cleaned_column_"),
        'apply_all': (apply_all_transformations, CLEANED_FOLDER, "cleaned_"),
        'clean_characters': (remove_special_characters, REMOVED_SPECIAL_CHARACTERS_FOLDER, "removed_special_characters_"),
        'convert_excel': (convert_excel, CONVERTED_EXCEL, "convert_to_excel_"),
        'convert_json': (convert_json, CONVERTED_JSON, "convert_to_json_"),
        'convert_parquet': (convert_parquet, CONVERTED_PARQUET, "convert_to_parquet_"),        
    }

    for action, (func, folder, prefix) in transformations.items():
        if action in request.form:
            df_transformed = func(df_preview)  # Exécuter la transformation
            if df_transformed is None:
                return render_template("traitement_csv.html", message=f"La transformation '{action}' a échoué.")

            # Vérifier si c'est un fichier ou un DataFrame
            if isinstance(df_transformed, str):
                return render_template("result.html", message=f"Nom de fichier généré : {df_transformed}", filename=os.path.basename(df_transformed))
            elif isinstance(df_transformed, pd.DataFrame):  # Si c'est un DataFrame
                columns = df_preview.columns.tolist()
                data = df_preview.values.tolist()
                transformed_filename = f"{prefix}{file.filename}"
                transformed_filepath = os.path.join(folder, transformed_filename)
                df_transformed.to_csv(transformed_filepath, index=False)
                columns = df_transformed.columns.tolist()  # Récupérer les noms de colonnes
                data = df_transformed.values.tolist()
                return render_template("result.html", data=data, columns=columns, encod=encoding, filename=transformed_filename)
            else:
                return render_template("traitement_csv.html", message=f"Erreur : '{action}' n'a pas retourné un format valide.")       
    return "Aucune action sélectionnée."

                ######################################Changer l'encodage du fichier csv
def changed(file_path):
   # Récupérer l'encodage choisi par l'utilisateur
    new_encoding = request.form.get("new_encoding", "utf-8")
    detected_encoding = detect_encoding(file_path)
    separator = detect_separator(file_path, detected_encoding)
    try:
        df = pd.read_csv(file_path, encoding=detected_encoding, sep=separator)
        new_filename = f"{new_encoding}_encoded_{os.path.basename(file_path)}"
        new_path = os.path.join(CHANGED_ENCODING_FOLDER, new_filename)
        df.to_csv(new_path, index=False, encoding=new_encoding, errors="replace")
        return df, detected_encoding, new_path, new_encoding    
    except Exception as e:
        return None, f"Erreur lors du changement d'encodage : {str(e)}", None

@app.route('/change_encoding', methods=['POST'])
def change_encoding_route():
    if 'file' not in request.files:
        return render_template("traitement_csv.html", message="Aucun fichier sélectionné.")
    file = request.files['file']
    # Sauvegarde du fichier
    original_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(original_path)
    result = changed(original_path)
    if result[0] is None:
        # Si le premier élément est None (erreur), alors afficher le message d'erreur
        return render_template("traitement_csv.html", message=result[1])
    df, detected_encoding, new_path, new_encoding = result
    if df is None:
        return render_template("traitement_csv.html", message=f"La transformation a retourné None.")
    if not isinstance(df, pd.DataFrame):
        return render_template("traitement_csv.html", message=f"Erreur : n'a pas retourné un DataFrame valide.") 
    message = f"Fichier encodé en {new_encoding} avec succès ! (Ancien encodage détecté : {detected_encoding}). Nom de fichier: {os.path.basename(new_path)}"
    return render_template('result.html', data=df.head(10).values.tolist(), message=message, filename=os.path.basename(new_path))

################################################## Fusionner plusieurs fichiers csv
def concat_csvs(file_paths):
    try:
        dfs = [] 
        # Vérification de l'existence des fichiers et lecture des CSV
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Le fichier {file_path} n'a pas été trouvé.")
            df = pd.read_csv(file_path)
            dfs.append(df)
        
        # Concaténation des DataFrames
        df_all = pd.concat(dfs, ignore_index=True)
        
        # Génération du nom de fichier de sortie
        new_filename = "concatened_" + "_".join([os.path.basename(path) for path in file_paths])
        new_path = os.path.join(CONCATENED_FOLDER, new_filename)
        df_all.to_csv(new_path, index=False)

        success_message = f"Fichiers fusionnés avec succès !"
        return df_all, success_message, new_path
    except Exception as e:
        return None, f"Erreur lors de la concaténation des fichiers : {str(e)}", None
  
@app.route('/concat_csv', methods=['POST'])
def concat_csv():
    if 'files' not in request.files:
        return render_template("traitement_csv.html", message="Aucun fichier sélectionné.")

    files = request.files.getlist('files')

    if len(files) < 2:  # On s'attend à au moins deux fichiers
        return render_template("traitement_csv.html", message="Veuillez sélectionner au moins deux fichiers CSV.")

    # Sauvegarde des fichiers
    file_paths = []
    for file in files:
        if file.filename == "":
            return render_template("traitement_csv.html", message="Veuillez sélectionner tous les fichiers CSV.")        
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(file_path)
        file_paths.append(file_path)
    result = concat_csvs(file_paths)
    if result[0] is None:
        # Si le premier élément est None (erreur), alors afficher le message d'erreur
        return render_template("traitement_csv.html", message=result[1])
    # Si tout va bien, on récupère les trois valeurs retournées
    df, success_message, new_path = result
    data = df.sort_values(by=df.columns[0])
    
    if df is None:
        return render_template("traitement_csv.html", message="La transformation a retourné None.")
    if not isinstance(df, pd.DataFrame):
        return render_template("traitement_csv.html", message="Erreur : n'a pas retourné un DataFrame valide.")
    return render_template('result.html', data=data.values.tolist(), message=success_message, filename=os.path.basename(new_path))

#################################### Compression de pdf

def compress_pdf_file(input_path, quality=50, dpi=100):
    """Compresse un fichier PDF en réduisant la qualité des images."""
    if not input_path.lower().endswith(".pdf"):
        raise ValueError("Le fichier fourni n'est pas un PDF valide.")
    
    output_path = os.path.join(COMPRESSED_FOLDER, os.path.basename(input_path))
    compressed_filename=os.path.basename(output_path)

    doc = pymupdf.open(input_path)
    # doc = fitz.open(input_path)
    new_doc = pymupdf.open()  # Nouveau PDF optimisé
    
    # Vérifier si le PDF est chiffré
    if doc.is_encrypted:
        raise ValueError("Le fichier PDF est chiffré et nécessite un mot de passe.")
    
    if doc.is_closed:
        raise ValueError("Le document a été fermé avant traitement.")
    
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)  # Charger la page
        images = page.get_images(full=True)  # Récupérer les images de la page
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)  # Créer une nouvelle page dans le PDF optimisé

        # Copier tout le contenu de la page originale
        new_page.show_pdf_page(new_page.rect, doc, page_index)
        
        for img_index, img in enumerate(images):
            xref = img[0]  # Référence de l'image
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]  # Extraire les données de l'image
            img_ext = base_image["ext"]  # Extension de l'image (par exemple "png", "jpeg")

            # Ouvrir l'image avec PIL et compresser en JPEG
            img_pil = Image.open(io.BytesIO(img_bytes))
            img_pil = img_pil.convert("RGB")  # S'assurer que l'image est en RGB

            # Réduire la résolution pour une meilleure compression
            img_pil.thumbnail((dpi, dpi))  # Réduction agressive de la taille

            img_io = io.BytesIO()
            img_pil.save(img_io, format="JPEG", quality=quality)  # Compression en JPEG avec le quality spécifié

            # Vérification et correction des valeurs pour éviter un rect vide ou infini
            x0, y0, x1, y1 = img[1], img[2], img[3], img[4]

            # Vérifier si les valeurs sont valides et bien ordonnées
            if not all(map(lambda v: isinstance(v, (int, float)), [x0, y0, x1, y1])):
                continue  # Ignore l'image si les coordonnées sont invalides

            # Vérifier si le rectangle est valide
            if x0 >= x1 or y0 >= y1:
                continue  # Ignore l'image si la taille est nulle ou incorrecte

            # Créer le rectangle sécurisé
            rect = fitz.Rect(x0, y0, x1, y1)
            new_page.insert_image(rect, stream=img_io.getvalue())  # Insérer l'image compressée dans le PDF

    # Sauvegarde optimisée
    new_doc.save(output_path, garbage=4, deflate=True)
    new_doc.close()
    
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    orig_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_path)
    ratio = (compressed_size / orig_size) * 100 if orig_size > 0 else 0
    return output_path, compressed_filename, orig_size, compressed_size, ratio

@app.route("/compression_valide_pdf", methods=["GET", "POST"])
def compress_pdf():
    if request.method == "POST":

        if "file" not in request.files:
            session["error_message"] = "Aucun fichier sélectionné."
            return redirect(url_for("compress_pdf"))

        file = request.files["file"]
        action = request.form.get("action")  # Récupérer le bouton cliqué
        filename = secure_filename(file.filename)
        orig_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(orig_path)

        try:
            result = compress_pdf_file(orig_path)
            output_path, compressed_filename, orig_size, compressed_size, ratio = result

            
            if action == "extract":
                text_path = extract_text_from_pdf(orig_path)
                text_name = os.path.basename(text_path)

                # Renvoyer un lien pour télécharger le texte extrait
                return render_template("result.html", text_filename=text_name, text_path=text_path)
            if action == "compres":
                if ratio >= 100:
                    session["error_message"] = "Compression inefficace : Le fichier compressé est plus grand ou égal à l'original."
                    return redirect(url_for("compress_pdf"))
                else:
                    return render_template(
                        "result.html",
                        filename=compressed_filename,
                        orig_size=orig_size,
                        compressed_size=compressed_size,
                        ratio=f"{ratio:.2f}%",
                        compressed_path=output_path,
                        ratio_class="green"
                    )

        except ValueError:
            session["error_message"] = "Erreur : Le fichier n'est pas un PDF valide."
            return redirect(url_for("compress_pdf"))

    # Récupère et supprime le message d'erreur de la session après affichage
    error_message = session.pop("error_message", None)
    return render_template("traitement_pdf.html", error_message=error_message)


#############################################Extraction du texte, d'images, des métadonnées d'un pdf

def extract_text_from_pdf(pdf_path):
    """Extrait le texte d'un PDF et l'enregistre dans un fichier .txt"""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])

 # Créer un fichier texte avec le même nom que le PDF dans le répertoire static
    text_filename = os.path.basename(pdf_path).replace(".pdf", ".txt")
    text_path = os.path.join(STATIC_FOLDER, text_filename)  # Sauvegarde dans le répertoire static

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    return text_path  # Retourne le chemin du fichier texte

# def extract_images_from_pdf(pdf_path):
#     doc = fitz.open(pdf_path)
#     images = []
#     for page_num in range(doc.page_count):
#         page = doc.load_page(page_num)
#         image_list = page.get_images(full=True)

#         for img in image_list:
#             xref = img[0]
#             base_image = doc.extract_image(xref)
#             image_bytes = base_image["image"]

#             # Convertir l'image en format PIL
#             image = Image.open(io.BytesIO(image_bytes))
#             images.append(image)
#     return images

    # # Sauvegarder les images extraites
    # for i, img in enumerate(images):
    #     img.save(f"image_{i}.png")

# def extract_metadata_from_pdf(pdf_path):
#     doc = fitz.open(pdf_path)
#     metadata = doc.metadata
#     return metadata

# def extract_text_from_pdf(pdf_path):
#    # Ouvrir le document PDF
#     doc = fitz.open(pdf_path)
#     text = ""

#     # Parcourir chaque page du PDF
#     for page_num in range(doc.page_count):
#         page = doc.load_page(page_num)  # Charger la page
#         try:
#             # Essayer d'extraire le texte
#             page_text = page.get_text("text")
#             text += page_text
#         except Exception as e:
#             # Capturer toute erreur d'encodage ou autre
#             print(f"Erreur lors de l'extraction du texte de la page {page_num + 1}: {e}")

#     # Fermer le document PDF après l'extraction
#     doc.close()

#     return text
############################################Cette route reçoit un fichier pdf
# @app.route('/upload_pdf', methods=['POST'])
# def upload_pdf():
#     if 'file' not in request.files:
#         return render_template("traitement_pdf.html", message="Aucun fichier sélectionné.")
    
#     file = request.files['file']
    
#     # Vérifier si le fichier est un PDF
#     if file and file.filename.endswith(".pdf"):
#         filename = secure_filename(file.filename)
#         original_filepath = os.path.join(UPLOAD_FOLDER, filename)
#         file.save(original_filepath)

#         # Vérifier quel bouton a été pressé et appliquer la transformation appropriée
#         transformations = {
#             'text': (extract_text_from_pdf, EXTRACTED_TEXT_PDF, "extracted_text_"),
#             'image': (extract_images_from_pdf, EXTRACTED_IMAGE_PDF, "extracted_img_"),
#             'metadata': (extract_metadata_from_pdf, EXTRACTED_METADATA_PDF, "extracted_metadata_"),
#         }

#         # Parcours de chaque transformation possible
#         for action, (func, folder, prefix) in transformations.items():
#             if action in request.form:
#                 # Appliquer la transformation
#                 extracted_data = func(original_filepath)  # Appeler la fonction d'extraction

#                 if extracted_data is None:
#                     return render_template("traitement_pdf.html", message=f"La transformation '{action}' a échoué.")
                
#                 # Si la transformation demande de retourner du texte extrait
#                 if action == 'text':
#                     return render_template("result.html", extracted_text=extracted_data, filename=filename)

#                 # Si c'est un fichier ou un DataFrame
#                 if isinstance(extracted_data, str):  # Fichier généré
#                     return render_template("result.html", message=f"Nom de fichier généré : {extracted_data}", filename=os.path.basename(extracted_data))
#                 elif isinstance(extracted_data, pd.DataFrame):  # Si c'est un DataFrame
#                     transformed_filename = f"{prefix}{file.filename}"
#                     transformed_filepath = os.path.join(folder, transformed_filename)
#                     extracted_data.to_csv(transformed_filepath, index=False)
#                     data = extracted_data.values.tolist()
#                     return render_template("result.html", data=data, filename=transformed_filename)
#                 else:
#                     return render_template("traitement_pdf.html", message=f"Erreur : '{action}' n'a pas retourné un format valide.")
        
#         return "Aucune action sélectionnée."


############################################# Ajouter du texte au pdf

def add_text_to_pdf_file(input_path, text, page_number=-1, font_size=12, color=(0, 0, 0)):
    """Ajoute du texte juste avant le footer, après le dernier mot de la page spécifiée."""
    
    doc = fitz.open(input_path)  
    output_path = os.path.join(ADDED_PDF, "added_" + os.path.basename(input_path))
    
    # Définir la page cible (dernière page par défaut)
    if page_number == -1:
        page_number = len(doc) - 1  
    if page_number < 0 or page_number >= len(doc):
        raise ValueError(f"Le PDF contient {len(doc)} pages. Impossible d'ajouter du texte à la page {page_number + 1}.")

    page = doc[page_number]

    # Récupérer la hauteur de la page pour positionner le texte
    footer_margin = 50
    page_height = page.rect.height  

    # Trouver la position du dernier bloc de texte
    blocks = page.get_text("blocks")  
    if blocks:
        last_block = sorted(blocks, key=lambda b: (b[1], b[0]))[-1]
        x, y = last_block[0], last_block[3] + font_size + 5  
        if y + font_size > page_height - footer_margin:
            y = page_height - footer_margin - font_size - 5  
    else:
        x, y = 50, page.rect.height - footer_margin - font_size  

    # Ajouter le texte
    page.insert_text((x, y), text, fontsize=font_size, color=color)

    doc.save(output_path)
    doc.close()
    return output_path, os.path.basename(output_path)

@app.route('/modify-pdf', methods=['POST'])
def modify_pdf():
    try:
        file = request.files.get("file")
        text = request.form.get("text")
        color = request.form.get("color", "black")
        pages_to_delete = request.form.get("pages")
        action = request.form.get("action")  # Récupérer le bouton cliqué

        if not file:
            return "Veuillez sélectionner un fichier PDF.", 400

        filename = secure_filename(file.filename)
        if not filename.lower().endswith(".pdf"):
            return "Veuillez sélectionner un fichier PDF.", 400

        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        # Dictionnaire des couleurs
        color_dict = {
            "black": (0, 0, 0),
            "red": (1, 0, 0),
            "blue": (0, 0, 1),
            "green": (0, 1, 0),
            "purple": (0.5, 0, 0.5)
        }
        selected_color = color_dict.get(color, (0, 0, 0))

        removed_pdf_path = None
        added_pdf_path = None

        # 🔹 Suppression des pages (si demandée)
        if action in ["delete_pages", "both"] and pages_to_delete:
            pages_to_delete = [int(p) - 1 for p in pages_to_delete.split(",") if p.strip().isdigit()]
            reader = PdfReader(input_path)
            writer = PdfWriter()

            for i in range(len(reader.pages)):
                if i not in pages_to_delete:
                    writer.add_page(reader.pages[i])

            removed_pdf_path = os.path.join(ADDED_PDF, "modified_" + filename)
            with open(removed_pdf_path, "wb") as output_pdf:
                writer.write(output_pdf)

        # 🔹 Ajout du texte (si demandé)
        if action in ["add_text", "both"] and text:
            pdf_to_edit = removed_pdf_path if removed_pdf_path else input_path
            added_pdf_path, added_filename = add_text_to_pdf_file(pdf_to_edit, text, color=selected_color)

        # 🔹 Renvoyer le bon fichier selon l’action choisie
        if action == "add_text" and added_pdf_path:
            return render_template("result.html", added_filename=added_filename, added_pdf_url=f"/view-pdf/{added_filename}")

        if action == "delete_pages" and removed_pdf_path:
            removed_filename=os.path.basename(removed_pdf_path)
            return render_template("result.html", removed_filename=removed_filename, removed_pdf_url=f"/view-pdf/{os.path.basename(removed_pdf_path)}")

        if action == "both" and added_pdf_path:
            return render_template(
                "result.html",
                # removed_and_add_filename=os.path.basename(removed_pdf_path),
                # removed_pdf_url=f"/view-pdf/{os.path.basename(removed_pdf_path)}",
                added_filename=added_filename,
                added_pdf_url=f"/view-pdf/{added_filename}"
            )

        return "Aucune modification n'a été effectuée.", 400

    except Exception as e:
        return f"Erreur lors du traitement du fichier : {str(e)}", 500
        
#######################################afficher l'apercu du pdf
@app.route('/view-pdf/<filename>')
def view_pdf(filename):
    file_path = os.path.join(ADDED_PDF, filename)
    return send_file(file_path, mimetype='application/pdf')


##################################################Téléchargement du fichier nettoyé (/download/<filename>)
@app.route('/download/<filename>')
def download_file(filename):
    # Vérifie dans quel dossier le fichier existe
    for folder in [FORMATTED_FOLDER, OUTPUT_FOLDER, ADDED_PDF, REMOVED_NULL_FOLDER, REMOVED_DUPLICATE_FOLDER, CLEANED_COLUMN_FOLDER,
    CLEANED_FOLDER, REMOVED_SPECIAL_CHARACTERS_FOLDER, CHANGED_ENCODING_FOLDER, COMPRESSED_FOLDER, CONVERTED_EXCEL, CONVERTED_JSON, 
    COMPRESSED_CSV, CONCATENED_FOLDER, CONVERTED_PARQUET, FORMATTED_MIN_FOLDER, STATIC_FOLDER, UPLOAD_FOLDER]:
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
    
    return "Fichier non trouvé", 404

################################################# Configuration pour l'envoi de mails via Gmail

#charge les variables d'env
load_dotenv()
api_key = os.getenv("API_KEY")
print(api_key)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# Route pour le formulaire
# Route pour le formulaire
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        telephone = request.form.get('phone')
        message = request.form.get('message')

        # Vérification des champs
        if not nom or not email or not telephone or not message:
            flash("Tous les champs doivent être remplis.", "danger")
            return redirect(url_for('contact') + "#contactForm")  # Rediriger vers l'ancre du formulaire


        # Création du message email
        msg = Message(
            'Nouveau message de contact',
            recipients=['yasmineprudence@yahoo.fr'],
            body=f"Nom: {nom}\nEmail: {email}\nTéléphone: {telephone}\nMessage: {message}"
        )

        try:
            mail.send(msg)
            flash("Email envoyé avec succès!", "success")
        except Exception as e:
            flash(f"Erreur lors de l'envoi de l'email: {str(e)}", "danger")
            print("Erreur d'envoi d'email:", str(e))

        return redirect(url_for('contact') + "#contactForm")  # Rediriger vers l'ancre du formulaire
    
    return render_template("index.html")

##########################################Exécution de l’application
# wsgi.py
if __name__ == '__main__':
    #host='0.0.0.0' permet d’accéder à l’application depuis d’autres appareils sur le même réseau
    #debug=True active le mode débogage pour voir les erreurs en temps réel.
    app.run(host='0.0.0.0', port=5000, debug=True)
   

