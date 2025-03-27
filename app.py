from PIL import Image
import chardet
import fitz
print(fitz.__file__)
from flask import Flask, flash, render_template, request, send_file,  redirect, url_for, session
import pandas as pd
import os
from werkzeug.utils import secure_filename
import re
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import pymupdf
from pdfminer.high_level import extract_text


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




#Crée ces dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, FORMATTED_FOLDER, ADDED_PDF, FORMATTED_MIN_FOLDER, REMOVED_NULL_FOLDER, REMOVED_DUPLICATE_FOLDER,
               CLEANED_COLUMN_FOLDER, CLEANED_FOLDER, CHANGED_ENCODING_FOLDER, REMOVED_SPECIAL_CHARACTERS_FOLDER, COMPRESSED_FOLDER, 
               CONVERTED_EXCEL, CONVERTED_JSON, COMPRESSED_CSV, CONCATENED_FOLDER, CONVERTED_PARQUET, EXTRACTED_IMAGE_PDF, EXTRACTED_METADATA_PDF,
               EXTRACTED_TEXT_PDF]:
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
        df = pd.read_csv(original_filepath, sep=separator, encoding=encoding, nrows=10)
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
            df_transformed = func(df)  # Exécuter la transformation
            if df_transformed is None:
                return render_template("traitement_csv.html", message=f"La transformation '{action}' a échoué.")

            # Vérifier si c'est un fichier ou un DataFrame
            if isinstance(df_transformed, str):
                return render_template("result.html", message=f"Nom de fichier généré : {df_transformed}", filename=os.path.basename(df_transformed))
            elif isinstance(df_transformed, pd.DataFrame):  # Si c'est un DataFrame
                transformed_filename = f"{prefix}{file.filename}"
                transformed_filepath = os.path.join(folder, transformed_filename)
                df_transformed.to_csv(transformed_filepath, index=False)
                data = df_transformed.values.tolist()
                return render_template("result.html", data=data, encod=encoding, filename=transformed_filename)
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
        filename = secure_filename(file.filename)
        orig_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(orig_path)

        try:
            result = compress_pdf_file(orig_path)
            output_path, compressed_filename, orig_size, compressed_size, ratio = result

            if ratio >= 100:
                session["error_message"] = "Compression inefficace : Le fichier compressé est plus grand ou égal à l'original."
                return redirect(url_for("compress_pdf"))

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
# # Création d'une image test
# img = Image.new("RGB", (100, 100), color="red")
# img_bytes = io.BytesIO()
# img.save(img_bytes, format="JPEG")

# # Réouverture de l'image
# img_bytes.seek(0)
# img_test = Image.open(img_bytes)
# img_test.show()

############################################# Ajouter du texte au pdf

def add_text_to_pdf_file(input_path, text, page_number=-1, font_size=12, color=(0, 0, 0)):
    """Ajoute du texte à la ligne suivant le dernier mot de la page, juste avant le footer."""

    doc = fitz.open(input_path)  
    output_path = os.path.join(ADDED_PDF, os.path.basename(input_path))
    added_filename = os.path.basename(output_path)

    # Si aucun numéro de page n'est précisé, ajouter le texte à la dernière page
    if page_number == -1:
        page_number = len(doc) - 1  

    # Vérifier si la page demandée existe
    if page_number < 0 or page_number >= len(doc):
        raise ValueError(f"Le PDF contient {len(doc)} pages. Impossible d'ajouter du texte à la page {page_number + 1}.")

    page = doc[page_number]  # Charger la page demandée

    # Extraire le texte existant sous forme de blocs
    blocks = page.get_text("blocks")  # Récupère les blocs de texte (contenu et positions)

    footer_margin = 50  # La marge avant le footer, ajustez si nécessaire
    page_height = page.rect.height  # Hauteur totale de la page

    if blocks:
        # Trouver la dernière ligne de texte
        last_block = sorted(blocks, key=lambda b: (b[1], b[0]))[-1]  # Trier par position Y puis X
        x, y = last_block[0], last_block[3]  # X reste le même, Y est la position en bas du bloc

        # Ajouter un petit espace sous le dernier texte
        y += font_size + 5  # Décalage de quelques pixels

        # Si la position Y du dernier texte est trop proche du footer, ajuster
        if y + font_size > page_height - footer_margin:
            y = page_height - footer_margin - font_size - 5  # Placer un peu au-dessus du footer
    else:
        # Si aucun texte trouvé, placer le texte en bas de la page
        x, y = 50, page.rect.height - footer_margin - font_size

    # Ajouter le texte avec la couleur spécifiée
    page.insert_text((x, y), text, fontsize=font_size, color=color)

    # Sauvegarde du fichier
    doc.save(output_path)
    doc.close()

    return output_path, added_filename

@app.route('/add-text-to-pdf', methods=['POST'])
def add_text():
    if "file" not in request.files or "text" not in request.form:
        return "Veuillez sélectionner un fichier PDF et saisir du texte."

    file = request.files["file"]
    text = request.form["text"]
    color = request.form.get("color", "black")  # Récupérer la couleur du texte, défaut = noir
    filename = secure_filename(file.filename)

    if not filename.lower().endswith(".pdf"):
        return "Veuillez sélectionner un fichier PDF."

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

  # Convertir la couleur sélectionnée en valeurs RGB
    color_dict = {
        "black": (0, 0, 0),
        "red": (1, 0, 0),
        "blue": (0, 0, 1),
        "green": (0, 1, 0),
        "purple": (0.5, 0, 0.5)
    }
    selected_color = color_dict.get(color, (0, 0, 0))  # Par défaut, noir

    # Ajouter du texte au PDF
    try:
        output_path, added_filename = add_text_to_pdf_file(input_path, text, color=selected_color)
        return render_template("result.html", filename=added_filename, output_path=output_path, pdf_url=f"/view-pdf/{added_filename}"  # URL du PDF modifié
        )
    except Exception as e:
        return f"Erreur lors du traitement du fichier : {str(e)}", 500

#######################################afficher l'apercu du pdf
@app.route('/view-pdf/<filename>')
def view_pdf(filename):
    file_path = os.path.join(ADDED_PDF, filename)
    return send_file(file_path, mimetype='application/pdf')


#############################################Extraction du texte, d'images, des métadonnées d'un pdf


def extract_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)

        for img in image_list:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Convertir l'image en format PIL
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)
    return images

    # # Sauvegarder les images extraites
    # for i, img in enumerate(images):
    #     img.save(f"image_{i}.png")

def extract_metadata_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    metadata = doc.metadata
    return metadata

def extract_text_from_pdf(pdf_path):
   # Ouvrir le document PDF
    doc = fitz.open(pdf_path)
    text = ""

    # Parcourir chaque page du PDF
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # Charger la page
        try:
            # Essayer d'extraire le texte
            page_text = page.get_text("text")
            text += page_text
        except Exception as e:
            # Capturer toute erreur d'encodage ou autre
            print(f"Erreur lors de l'extraction du texte de la page {page_num + 1}: {e}")

    # Fermer le document PDF après l'extraction
    doc.close()

    return text
############################################Cette route reçoit un fichier pdf
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return render_template("traitement_pdf.html", message="Aucun fichier sélectionné.")
    
    file = request.files['file']
    
    # Vérifier si le fichier est un PDF
    if file and file.filename.endswith(".pdf"):
        filename = secure_filename(file.filename)
        original_filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(original_filepath)

        # Vérifier quel bouton a été pressé et appliquer la transformation appropriée
        transformations = {
            'text': (extract_text_from_pdf, EXTRACTED_TEXT_PDF, "extracted_text_"),
            'image': (extract_images_from_pdf, EXTRACTED_IMAGE_PDF, "extracted_img_"),
            'metadata': (extract_metadata_from_pdf, EXTRACTED_METADATA_PDF, "extracted_metadata_"),
        }

        # Parcours de chaque transformation possible
        for action, (func, folder, prefix) in transformations.items():
            if action in request.form:
                # Appliquer la transformation
                extracted_data = func(original_filepath)  # Appeler la fonction d'extraction

                if extracted_data is None:
                    return render_template("traitement_pdf.html", message=f"La transformation '{action}' a échoué.")
                
                # Si la transformation demande de retourner du texte extrait
                if action == 'text':
                    return render_template("result.html", extracted_text=extracted_data, filename=filename)

                # Si c'est un fichier ou un DataFrame
                if isinstance(extracted_data, str):  # Fichier généré
                    return render_template("result.html", message=f"Nom de fichier généré : {extracted_data}", filename=os.path.basename(extracted_data))
                elif isinstance(extracted_data, pd.DataFrame):  # Si c'est un DataFrame
                    transformed_filename = f"{prefix}{file.filename}"
                    transformed_filepath = os.path.join(folder, transformed_filename)
                    extracted_data.to_csv(transformed_filepath, index=False)
                    data = extracted_data.values.tolist()
                    return render_template("result.html", data=data, filename=transformed_filename)
                else:
                    return render_template("traitement_pdf.html", message=f"Erreur : '{action}' n'a pas retourné un format valide.")
        
        return "Aucune action sélectionnée."

##################################################Téléchargement du fichier nettoyé (/download/<filename>)
@app.route('/download/<filename>')
def download_file(filename):
    # Vérifie dans quel dossier le fichier existe
    for folder in [FORMATTED_FOLDER, OUTPUT_FOLDER, ADDED_PDF, REMOVED_NULL_FOLDER, REMOVED_DUPLICATE_FOLDER, CLEANED_COLUMN_FOLDER, CLEANED_FOLDER, REMOVED_SPECIAL_CHARACTERS_FOLDER, CHANGED_ENCODING_FOLDER, COMPRESSED_FOLDER, CONVERTED_EXCEL, CONVERTED_JSON, COMPRESSED_CSV, CONCATENED_FOLDER, CONVERTED_PARQUET, FORMATTED_MIN_FOLDER]:
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
   

