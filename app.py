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

#Crée une instance de Flask
app = Flask(__name__)
app.secret_key = "secretkey"  # Nécessaire pour utiliser `session`

#Définit les dossiers où stocker les fichiers envoyés et nettoyés
UPLOAD_FOLDER = "upload_data"
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


#Crée ces dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, FORMATTED_FOLDER, FORMATTED_MIN_FOLDER, REMOVED_NULL_FOLDER, REMOVED_DUPLICATE_FOLDER, CLEANED_COLUMN_FOLDER, CLEANED_FOLDER, CHANGED_ENCODING_FOLDER, REMOVED_SPECIAL_CHARACTERS_FOLDER, COMPRESSED_FOLDER, CONVERTED_EXCEL, CONVERTED_JSON, COMPRESSED_CSV, CONCATENED_FOLDER, CONVERTED_PARQUET]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/github')
def github():
    return redirect("https://github.com/jasminePrudence/Traitement-de-donn-es")

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

###################################################Compression de fichier csv
def compress_pdf(input_path, output_path, quality=2):
  
    try:
        # Ouvre le fichier PDF
        doc = fitz.open(input_path)
        image_data = []

        # Variable pour vérifier si des images ont été trouvées
        images_found = False

        # Compression des images
        for page_num, page in enumerate(doc, start=1):
            images = page.get_images(full=True)

            if not images:
                continue  # Si la page ne contient pas d'images, on passe à la page suivante

            # Si des images sont présentes, on les compresse
            for img in images:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)

                if pix.width == 0 or pix.height == 0:
                    # Si l'image n'a pas de dimensions valides, on la saute
                    continue

                orig_size = len(pix.tobytes())
                print(orig_size)

                if pix.n >= 4:  # Si l'image est en RGBA ou CMYK, on la convertit en RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                # Convertir l'image en JPEG avec le niveau de qualité souhaité
                img_data = pix.tobytes("jpeg", quality=quality)
                doc.update_image(xref, stream=img_data)

                new_size = len(img_data)

                image_data.append({
                    "Page": page_num,
                    "XRef": xref,
                    "Original Size (bytes)": orig_size,
                    "Compressed Size (bytes)": new_size,
                    "Compression Ratio": round(new_size / orig_size, 2) if orig_size != 0 else 0
                })

                pix = None  # Libérer la mémoire de l'objet pixmap après l'avoir utilisé

            images_found = True  # Des images ont été trouvées et traitées

        # Avant de sauvegarder le fichier, calculons la taille du fichier PDF avant et après compression
        orig_size_pdf = os.path.getsize(input_path)  # Taille du fichier d'origine
        new_size_pdf = None

        if images_found:
            # Sauvegarder le PDF après la compression des images
            doc.save(output_path, garbage=4, clean=True)
            doc.close()

            # Calculer la taille du fichier après la compression
            new_size_pdf = os.path.getsize(output_path)  # Taille du fichier après compression

            return {
                "image_data": image_data,
                "Original Size (PDF bytes)": orig_size_pdf,
                "Compressed Size (PDF bytes)": new_size_pdf,
                "Compression Ratio (PDF)": round(new_size_pdf / orig_size_pdf, 2) if orig_size_pdf != 0 else 0
            }
        else:
            # Si aucune image n'a été trouvée, sauvegarder le PDF sans modification
            doc.save(output_path, garbage=4, clean=True)
            doc.close()

            return {
                "message": "Aucune image à compresser dans ce PDF.",
                "Original Size (PDF bytes)": orig_size_pdf,
                "Compressed Size (PDF bytes)": orig_size_pdf,
                "Compression Ratio (PDF)": 1.0  # Pas de compression car il n'y avait pas d'images
            }

    except Exception as e:
        # Si une erreur se produit, la fonction retourne une erreur avec un message approprié
        return {"error": str(e)}

def format_filename(filename):
    # Supprimer l'extension du fichier
    name, ext = os.path.splitext(filename)  
    # Remplacer les espaces et caractères spéciaux par des underscores
    formatted_name = re.sub(r'[^\w]+', '_', name)
    # Retourner le nom formaté avec l'extension
    return f"{formatted_name}{ext}"

############################################Cette route reçoit un fichier pdf
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return render_template("traitement_pdf.html", message="Aucun fichier sélectionné.")
    
    file = request.files['file']
    
    if file and file.filename.endswith(".pdf"):

        filename = secure_filename(format_filename(file.filename))
        original_filepath = save_file(UPLOAD_FOLDER, filename, file)
        compressed_filename = f"compressed_{filename}"
        compressed_filepath = os.path.join(FORMATTED_FOLDER, compressed_filename)

        
        try:
            data = compress_pdf(original_filepath, compressed_filepath, quality=2)
            image_data, orig_size_pdf, new_size_pdf = data    # 
    
        except Exception as e:
            return render_template("traitement_pdf.html", message="Erreur lors du traitement du fichier.")
        print(data)
        return render_template("traitement_pdf.html", end_data=orig_size_pdf, filename=compressed_filename, download_link=f"/download/{compressed_filename}")

    return render_template("traitement_pdf.html", message="Format de fichier non autorisé.")

#Téléchargement du fichier nettoyé (/download/<filename>)
@app.route('/download/<filename>')
def download_file(filename):
    # Vérifie dans quel dossier le fichier existe
    for folder in [FORMATTED_FOLDER, REMOVED_NULL_FOLDER, REMOVED_DUPLICATE_FOLDER, CLEANED_COLUMN_FOLDER, CLEANED_FOLDER, REMOVED_SPECIAL_CHARACTERS_FOLDER, CHANGED_ENCODING_FOLDER, COMPRESSED_FOLDER, CONVERTED_EXCEL, CONVERTED_JSON, COMPRESSED_CSV, CONCATENED_FOLDER, CONVERTED_PARQUET, FORMATTED_MIN_FOLDER]:
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
   

