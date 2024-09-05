from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from datetime import timedelta
from werkzeug.utils import secure_filename
from models import db, User, Plant, Comment, email_exists, username_exists, username_count, get_user
from models import password_count, email_count, get_plants, plants_saved_count, get_reviews
from usable import watering_message, truncate_words, generate_category, get_plant_uses, get_google_uses, get_plant_uses_family, get_plant_description_wikipedia
from usable import check_password, search_images_and_encode_first
import urllib.parse
import base64
import requests
import json
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://nyameget:xU9xKSe8zsSaeLqrUeotCAsdWNTzSwXX@dpg-cr938hq3esus73bfgb7g-a.oregon-postgres.render.com/dbname_skju'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '1567tay'
app.permanent_session_lifetime = timedelta(days=10)
app.secret_key = '1567tay'
UPLOAD_FOLDER = 'static/files'

db.init_app(app)

# Plant.id API endpoint
PLANT_ID_API_URL = "https://plant.id/api/v3/identification"
url = "https://plant.id/api/v3/identification?details=common_names,url,description,taxonomy,rank,gbif_id,inaturalist_id,image,synonyms,edible_parts,watering&language=en"

# Replace with your Plant.id API token
PLANT_ID_API_KEY_OLD = "SMVUfdDn8bs2BPxl5m9JYXSnGFOVIaRzAY65DIm9NBTKNJfG7p"
PLANT_ID_API_KEY = "G0SyXknxTXJD0R8DyS5rVWlL9A05s8VrGFaXSGGEmHznnOho1u"

@app.route('/', methods=['GET'])
def welcome():
    if 'username'in session:
        flash('User has already logged in', 'info')
        return redirect(url_for('home'))
    theme = session.get('theme', 'light')
    return render_template('welcome.html', data={'theme':theme})

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    try:
        if request.method == 'GET':
            if 'username' in session:
                # The user has logged and it hasnt been 10 days yet
                flash('User has already logged in', 'info')
                return redirect(url_for('home'))
            theme = session.get('theme', 'light')
            return render_template('signin.html', data={'theme':theme})
        elif request.method == 'POST':
            # Gets User log in info
            username = str(request.form['username']).strip()
            password = str(request.form['password']).strip()
            # Checks if user is in the system
            if username_exists(username):
                user = get_user(username)
                if (username == user.username) and (password == user.password):
                    # Successfully logged in
                    session['username'] = username
                    session['password'] = password
                    session['email'] = user.email
                    flash('Login successful', 'success')
                    return redirect(url_for('home'))
                else:
                    # Wrong details
                    flash('Wrong credentials', 'warning')
                    return redirect(url_for('signin'))
            else:
                # No account 
                flash('User has no account', 'info')
                return redirect(url_for('signup'))
    except:
        # Checks if user has logged in before
        if 'username' in session:
            flash('User has already logged in', 'info')
            return redirect(url_for('home'))
        # Error Occured
        flash('Error occured try again', 'danger')
        return redirect(url_for('signin'))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'GET':
            if 'username' in session:
                # The user has logged and it hasnt been 10 days yet
                flash('User has already logged in', 'info')
                return redirect('home')
            theme = session.get('theme', 'light')
            return render_template('signup.html', data={'theme': theme})
        elif request.method == 'POST':
            # Gets users data to be stored in the database
            name = str(request.form['name']).strip()
            username = str(request.form['username']).strip()
            email = str(request.form['email']).lower().strip()
            password = str(request.form['password']).strip()
            # Checks if password is greater or equal to 8
            if len(password) < 8: 
                flash('Password is less than minimum length (8)', 'danger')
                return redirect(url_for('signup'))
            # Checks if password contains a letter, number and a symbol
            if not check_password(password):
                flash('Password must contain Letters, Numbers and Symbols', 'danger')
                return redirect(url_for('signup'))
            # Check if username is taken
            userCount = username_count(username)
            # Check if email is taken
            emailCount = email_count(email)
            # Check if password is taken
            passwordCount = password_count(password)
            if userCount == 0:
                if emailCount == 0:
                    if passwordCount == 0:
                        # Store user data and redirect to signin page 
                        new_user = User(username=username, name=name, email=email, password=password)
                        db.session.add(new_user)
                        db.session.commit()
                        flash('User created successfully', 'success')
                        return redirect(url_for('signin'))
                    else:
                        # Password is taken
                        flash('Password has been used', 'warning')
                        return redirect(url_for('signup'))
                else:
                    # Email is taken
                    flash('Email has been used', 'warning')
                    return redirect(url_for('signup'))
            else:
                # Have an account
                flash('User has an account', 'info')
                return redirect(url_for('signin'))
    except:
        if 'username' in session:
            # An error occured during signup but user has already logged in in the past 10 days
            flash('User has already logged in', 'info')
            return redirect(url_for('home'))
        # User has no account and an error occured during the signup process
        flash('Error occured please try again', 'danger')
        return redirect(url_for('signup'))

@app.route("/home", methods=['GET'])
def home():
    try:
        if 'username' in session:
            theme = session.get('theme', 'light')
            return render_template('home.html', data={'active_page': 'home', 'theme': theme})
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))
    except:
        if 'username' in session:
            # An error occured
            flash('User has already logged in', 'info')
            return redirect(url_for('home'))
        # Not logged in
        flash('user has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route("/profile", methods=['GET'])
def profile():
    try:
        if 'username' in session:
            username = session['username']
            user = get_user(username)
            plant_count = plants_saved_count(username)
            userInfo = {
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'upload': plant_count
            }
            theme = session.get('theme', 'light')
            return render_template('profile.html', data={'user':userInfo, 'active_page': 'profile', 'theme': theme})
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))
    except:
        if 'username' in session:
            # An error occured
            flash('An error occured', 'danger')
            return redirect(url_for('profile'))
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route("/setting", methods=['GET', 'POST'])
def setting():
    try:
        if request.method == 'GET':
            if 'username' in session:
                theme = session.get('theme', 'light')
                username = session['username']
                email = session['email']
                return render_template('setting.html', data={'active_page': 'setting', 'theme': theme, 'email': email, 'username': username})
            # Not logged in
            flash('User has not logged in', 'info')
            return redirect(url_for('signin'))
        elif request.method == 'POST':
            # Handle form submission here
            username = session['username']
            if 'theme' in request.form:
                theme = str(request.form['theme']).strip()
                session['theme'] = theme
                return redirect(url_for('home'))
            elif 'decision' in request.form:
                decision = str(request.form['decision']).strip()
                if decision == 'yes':
                    user = get_user(username)
                    # Assuming `get_plants` returns a list of plant objects
                    plants = get_plants(username)
                    if user:
                        # Delete all associated plants
                        if plants:
                            for plant in plants:
                                db.session.delete(plant)
                        # Delete the user
                        db.session.delete(user)
                        # Commit the transaction
                        db.session.commit()
                        flash('User\'s data has been successfully deleted', 'success')
                        return redirect(url_for('logout'))
                    
                    flash('User not found', 'danger')
                    return redirect(url_for('logout'))
            elif 'rate' in request.form:
                rate = int(request.form['rate'])
                feedback = str(request.form['feedback']).strip()
                new_review = Comment(comment=feedback, rate=rate, username=username)
                db.session.add(new_review)
                db.session.commit()
                flash('Review submitted successfully', 'success')
                return redirect(url_for('home'))
    except Exception as e:
        if 'username' in session:
            # An error occured
            flash('Error occured please try again', 'danger')
            print(str(e))
            return redirect(url_for('setting'))
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route("/search", methods=['GET', 'POST'])
def search():
    try:
        if request.method == 'GET':
            if 'username' in session:
                theme = session.get('theme', 'light')
                return render_template('search.html', data={'theme': theme, 'active_page': ''})
            flash('User has not signed in', 'danger')
            return redirect(url_for('signin'))
        elif request.method == 'POST':
            plant_name = request.form['plant_name']
            search_url = f"https://plant.id/api/v3/kb/plants/name_search?q={plant_name}&thumbnails=true"
            print(search_url)
            headers = {
                'Api-Key': PLANT_ID_API_KEY,
                'Content-Type': 'application/json'
            }
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                entities = data.get('entities', [])
                if entities:
                    entity_result = []
                    for entity in entities:
                        if entity['matched_in_type'] == 'synonym':
                            continue
                        access_token = entity['access_token']
                        image_base64 = entity['thumbnail']
                        image_url = f"data:image/jpeg;base64,{image_base64}"
                        plant_info_url = f"https://plant.id/api/v3/kb/plants/{access_token}?details=common_names,url,description,taxonomy,rank,gbif_id,inaturalist_id,image,synonyms,edible_parts,watering&language=en"
                        plant_info_response = requests.get(plant_info_url, headers=headers)
                        result = plant_info_response.json()
                        if result['watering']:
                            irrigation_info = watering_message(result['watering'])
                        if result['common_names']:
                            # This gets the scientific name of the plant
                            botanical_name = result['name']
                            # This gets the family of the plant
                            family = result['taxonomy']['family']
                            plant_uses = None
                            # Check uses for each common name
                            for common_name in result['common_names']:
                                if common_name.lower() == family.lower():
                                    common_name = botanical_name
                                plant_uses = get_plant_uses(common_name, botanical_name)
                                if plant_uses is not None:
                                    break
                            # If plant uses not found for any common name, try Google search
                            if plant_uses is None:
                                plant_uses = get_google_uses(common_names[0])
                        else:
                            if len(result) == 1:
                                common_names = result['common_names']
                                common_name = common_names[0]
                                if common_names:
                                    # This gets the scientific name of the plant
                                    botanical_name = result['name']
                                    # This gets the family of the plant
                                    family = result['taxonomy']['family']
                                    plant_uses = None
                                    # Check uses for each common name
                                    for common_name in common_names:
                                        if common_name.lower() == family.lower():
                                            common_name = botanical_name
                                        plant_uses = get_plant_uses(common_name, botanical_name)
                                        if plant_uses is not None:
                                            break
                                    # If plant uses not found for any common name, try Google search
                                    if plant_uses is None:
                                        plant_uses = get_google_uses(common_names[0])
                            elif len(result) == 1 and result['common_names'] is None:
                                family_name = result['taxonomy']['family']
                                botanical_name = result['name']
                                plant_uses, common_name = get_plant_uses_family(family_name, botanical_name)
                                result['common_names'] = [common_name]
                            else:
                                print("No common names found in the classification results.")

                        entity_result.append({
                            'image_url': image_url,
                            'plant_info': result, 
                            'plant_uses': plant_uses,
                            'irrigation_info': irrigation_info
                        })
                    plant_details = []
                    for plant in entity_result:
                    # Ensure plant.plant_info is not None
                        if plant['plant_info'] is not None:
                        # This gets the result portion of the response
                            result = plant['plant_info']
                        # Ensure result is not None
                            if result is not None:
                                # Gets the common name of the plant
                                if result['common_names'] is not None:
                                    common_name = result['common_names'][0]
                                    # Gets the name of the plant
                                    plant_name = result['name']                            
                                # Gets the taxonomy of the plant
                                taxonomy = result['taxonomy']
                                list_taxonomy = list(taxonomy.items())[::-1]
                                reversed_taxonomy = {key: value for key, value in list_taxonomy}
                                # Gets the description of the plant
                                if result['description']:
                                    description = result['description']['value']
                                description = truncate_words(description, 60)
                                # Checks if  the plant is edible
                                edible_parts = result['edible_parts']
                                # Checks the watering conditions
                                watering = result['watering']
                                irrigation_info = watering_message(watering)
                                identification_results = {
                                    'name': plant_name,
                                    'common_name': common_name,
                                    'taxonomy': reversed_taxonomy,
                                    'description': description,
                                    'edible_part': edible_parts,
                                    'watering': irrigation_info
                                }
                                image_result = search_images_and_encode_first(common_name)  
                                if image_result:
                                    image_url = f"data:image/jpeg;base64,{image_result}"
                                else:
                                    image_url = plant['image_url']
                                plant_uses = plant['plant_uses']
                                if isinstance(plant_uses, set):
                                    plant_uses = plant_uses
                                    plant_uses_type = 'set'
                                elif isinstance(plant_uses, dict):
                                    plant_uses = plant_uses
                                    plant_uses = {key: value for key, value in list(plant_uses.items())[::-1]}
                                    plant_uses_type = 'dict'
                                plant_details.append({
                                    'image_url': image_url,
                                    'plant_data': identification_results,
                                    'plant_uses': plant_uses,
                                    'plant_uses_type': plant_uses_type
                                })  
                    theme = session.get('theme', 'light')
                    return render_template('search_result.html', data={'active-page': '', 'plant': plant_details, 'theme': theme})
    except  Exception as e:
        print(f"An error occurred: {str(e)}")
        print(logging.exception(e))
        flash('An error occured please try again', 'danger')
        return redirect(url_for('search'))
                                                
@app.route("/about", methods={"GET"})
def about():
    try:
        if 'username' in session:
            theme = session.get('theme', 'light')
            return render_template('about.html', data= {"active_page": 'about', 'theme': theme})
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))
    except:
        if 'username' in session:
            flash('An error occured please try again', 'danger')
            return redirect(url_for('about'))
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    try:
        if request.method == 'GET':
            if 'username' in session:
                theme = session.get('theme', 'light')
                return render_template('editinfo.html', data = {'active_page': '', 'theme': theme})
            # Not logged in
            flash('User has not logged in', 'info')
            return redirect(url_for('signin'))
        elif request.method == 'POST':
            choice = str(request.form['choice'])
            userPassword = session['password']
            username = session['username']
            user = get_user(username)
            if choice == 'password':
                oldPassword = str(request.form['oldPassword']).strip()
                newPassword = str(request.form['newPassword']).strip()
                passwordConfirmation = str(request.form['newPasswordConfirmation']).strip()
                if len(newPassword) < 8 or len(passwordConfirmation) < 8:
                    flash('Password less than 8', 'danger')
                    return redirect(url_for('edit'))
                if not check_password(newPassword) and not check_password(passwordConfirmation):
                    flash('Password must contain Letters, Numbers and Symbols', 'danger')
                    return redirect(url_for('edit'))
                passwordCount = password_count(newPassword)
                if oldPassword == userPassword:
                    if newPassword == oldPassword:
                        # Old password used as new
                        flash('New password is the same as old', 'warning')
                        return redirect(url_for('edit'))
                    if newPassword != passwordConfirmation:
                        # Password entered do not match
                        flash('Password mismatch', 'warning')
                        return redirect(url_for('edit'))
                    if passwordCount != 0:
                        flash('Password has been used', 'warning')
                        return redirect(url_for('edit'))
                    user.password = newPassword
                    db.session.commit()
                    # Updated successfully
                    session['password'] = newPassword
                    flash('Password successfully updated', 'success')
                    return redirect(url_for('home'))
                else:
                    # Password does not match
                    flash('Password mismatch', 'warning')
                    return redirect(url_for('edit'))
            elif choice == 'email':
                oldPassword = str(request.form['oldPassword']).strip()
                oldEmail = str(request.form['oldEmail']).lower().strip()
                newEmail = str(request.form['newEmail']).lower().strip()
                emailCount = email_count(newEmail)
                if oldPassword == userPassword:
                    if session['email'] == newEmail:
                        # Old email used as new
                        flash('New email is the same as old', 'warning')
                        return redirect(url_for('edit'))
                    if emailCount != 0:
                        flash('Email has been used', 'warning')
                        return redirect(url_for('edit'))
                    user.email = newEmail
                    db.session.commit()
                    session['email']  = newEmail
                    # Updated successfully
                    flash('Email has been successfully updated', 'success')
                    return redirect(url_for('home'))
                else:
                    # Password does not match
                    flash('Password mismatch', 'warning')
                    return redirect(url_for('edit'))              
    except:
        if 'username' in session:
            # An error occured
            flash('An error occured please try again', 'danger')
            return redirect(url_for('edit'))
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route("/scan", methods=['GET'])
def scan():
    try:
        if 'username' in session:
            theme = session.get('theme', 'light')
            return render_template('scan.html', data={'active_page': '', 'theme': theme})
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))
    except:
        if 'username' in session:
            # An error occured
            flash('An error occured please try again', 'danger')
            return redirect(url_for('scan'))
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        # Check if the POST request has a file part
        if 'image' not in request.files:
            # No file part
            flash('There is no file part', 'warning')
            return redirect(url_for('scan'))
        # Gets the image file from the form
        file = request.files['image']
        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            # Empty File
            flash('File is empty', 'warning')
            return redirect(url_for('scan'))
        try:
            # Read the image file and convert it to base64
            image_file = file.read()
            image_data = base64.b64encode(image_file).decode('utf-8')
            # Construct the base64 image string with appropriate data:image MIME type
            base64_image_string = f"data:image/jpeg;base64,{image_data}"
            payload = json.dumps({
                "images": [
                   base64_image_string
                ],
                "similar_images": True,
                "health": "all"
            })

            headers = {
                'Api-Key': PLANT_ID_API_KEY,
                'Content-Type': 'application/json'
            }
            # This integrates the plant.id api
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 201:
                # Turns the response into JSON
                plant_info = response.json()
                print(plant_info)
                # This gets the result portion of the response
                result = plant_info['result']
                # This gets the is_plant portion of the response
                is_plant = result['is_plant']
                # Gets the probability of the image containing a plant
                plant_probability = is_plant['probability']
                # Checks if a plant is in the image
                plant_binary = is_plant['binary']
                if plant_binary:
                    # This gets the common name of the plant
                    common_names = result['classification']['suggestions'][0]['details']['common_names']
                    if common_names:
                        # This gets the scientific name of the plant
                        botanical_name = result['classification']['suggestions'][0]['name']
                        # This gets the family of the plant
                        family = result['classification']['suggestions'][0]['details']['taxonomy']['family']
                        plant_uses = None
                        # Check uses for each common name
                        for common_name in common_names:
                            if common_name.lower() == family.lower():
                                common_name = botanical_name
                            plant_uses = get_plant_uses(common_name, botanical_name)
                            if plant_uses is not None:
                                break
                        # If plant uses not found for any common name, try Google search
                        if plant_uses is None:
                            plant_uses = get_google_uses(common_names[0])
                    else:
                        if len(result['classification']['suggestions']) > 1:
                            common_names = result['classification']['suggestions'][1]['details']['common_names']
                            common_name = common_names[0]
                            if common_names:
                                # This gets the scientific name of the plant
                                botanical_name = result['classification']['suggestions'][0]['name']
                                # This gets the family of the plant
                                family = result['classification']['suggestions'][0]['details']['taxonomy']['family']
                                plant_uses = None
                                # Check uses for each common name
                                for common_name in common_names:
                                    if common_name.lower() == family.lower():
                                        common_name = botanical_name
                                    plant_uses = get_plant_uses(common_name, botanical_name)
                                    if plant_uses is not None:
                                        break
                                # If plant uses not found for any common name, try Google search
                                if plant_uses is None:
                                    plant_uses = get_google_uses(common_names[0])
                        elif len(result['classification']['suggestions']) == 1 and result['classification']['suggestions'][0]['details']['common_names'] is None:
                            family_name = result['classification']['suggestions'][0]['details']['taxonomy']['family']
                            botanical_name = result['classification']['suggestions'][0]['name']
                            plant_uses, common_name = get_plant_uses_family(family_name, botanical_name)
                            result['classification']['suggestions'][0]['details']['common_names'] = [common_name]
                        else:
                            print("No common names found in the classification results.")
                    # Saves the plant into the plants table
                    new_plant = Plant(filename=file.filename, image_data=image_file, plant_info=plant_info, plant_uses=plant_uses, username=session['username'])
                    db.session.add(new_plant)
                    db.session.commit()
                    print("Saved Successfully")
                    # Redirect to the results page with the image URL and identification results
                    flash('Image saved successfully', 'success')
                    return redirect(url_for('results', image_id=new_plant.id))
                # Image does not contain plant
                flash('Image does not contain a plant', 'warning')
                return redirect(url_for('scan'))
            elif response.status_code == 200:
                data = response.json()
                print(data)
            # Invalid response returned
            theme = session.get('theme', 'light')
            return render_template('apierror.html', data={'error':jsonify({'error': 'Failed to identify plant'}), 'theme':theme})
        except Exception as e:
            theme = session.get('theme', 'light')
            return render_template('apierror.html', data={'error':jsonify({'error': str(e)}), 'theme':theme})
        
@app.route('/results/<int:image_id>')
def results(image_id):
    # Retrieve the image and identification results from the database
    image = Plant.query.get_or_404(image_id)
    # This checks the type of data it is
    if isinstance(image.plant_uses, set):
        plant_uses = image.plant_uses
        plant_uses_type = 'set'
    else:
        plant_uses = image.plant_uses
        plant_uses = {key: value for key, value in list(plant_uses.items())[::-1]}
        plant_uses_type = 'dict'
    # This gets the result of the identification
    result = image.plant_info['result']
    # Gets the classification portion of the response
    classification = result['classification']
    if len(result['disease']['suggestions'])  == 0:
        disease_category = ''
        disease_common_name = 'None'
        disease_description = 'None'
        disease_name = 'None'
    else: 
        # Gets the disease suggestion
        disease = result['disease']['suggestions'][0]
        # Generates the category of severity
        disease_category = generate_category(disease['probability'])
        # Gets the details of the disease
        disease_details = disease['details']
        # Gets the disease description
        disease_description = disease_details['description']
        # Gets the plant disease common name 
        disease_name = disease['name']
        if disease_details['common_names'] is not None:
            disease_common_name = disease_details['common_names'][0]
        else:
            disease_common_name = 'None'
    # Gets the first suggestion in the response
    suggestions = classification['suggestions'][0]
    # Gets the probabilty of the plant in the images similiarity
    plant_prob = suggestions['probability']
    # Gets the similiar images in the response 
    similar_images = suggestions['similar_images']
    # Gets the details portion of the response
    details = suggestions['details']
    # Gets the common name of the plant
    if details['common_names'] is not None:
        common_name = details['common_names'][0]
        # Gets the name of the plant
        plant_name = suggestions['name']
    elif len(result['classification']['suggestions']) == 1 and details['common_names'] is None: 
        common_name = details['common_names']
        plant_name = suggestions['name']
    else:
        common_name = result['classification']['suggestions'][1]['details']['common_names'][0]
        plant_name = result['classification']['suggestions'][1]['name']
    # Gets the taxonomy of the plant
    taxonomy = details['taxonomy']
    list_taxonomy = list(taxonomy.items())[::-1]
    reversed_taxonomy = {key: value for key, value in list_taxonomy}
    # Gets the description of the plant
    if details['description']:
        description = details['description']['value']
    elif len(result['classification']['suggestions']) == 1 and result['classification']['suggestions'][0]['details']['description'] is None:
        description = get_plant_description_wikipedia(common_name)
        if description is None:
            description = get_plant_description_wikipedia(plant_name)
    else: 
        description = result['classification']['suggestions'][1]['details']['description']['value']
    # Gets the synonyms of the plants name
    synonyms = details['synonyms']
    # Checks if  the plant is edibles
    edible_parts = details['edible_parts']
    # Checks the watering conditions
    watering = details['watering']
    irrigation_info = watering_message(watering)
    # Encodes the image in base64
    image_base64 = base64.b64encode(image.image_data).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{image_base64}"
    identification_results = {
        'name': plant_name,
        'common_name': common_name,
        'taxonomy': reversed_taxonomy,
        'description': description,
        'edible_part': edible_parts,
        'watering': irrigation_info,
        'disease_category': disease_category,
        'disease_description': disease_description,
        'disease_common_name': disease_common_name.capitalize(),
        'disease_name': disease_name.capitalize(),
        'plant_uses': plant_uses,
        'plant_uses_type': plant_uses_type
    }
    theme = session.get('theme', 'light')
    # Render the results page with the image and identification results
    return render_template('result.html', data={'image_url':image_url, 'results':identification_results, 'theme': theme})

@app.route("/history", methods=['GET'])
def history():
    try:
        if request.method == 'GET':
            if 'username' in session:
                username = session['username']
                savedPlantCount = plants_saved_count(username)
                if savedPlantCount == 0:
                    # No plant saved
                    flash('No plant identfied yet', 'info')
                    return redirect(url_for('home'))
                # Gets all the plants saved in the plants table
                savedPlants = get_plants(username)
                # Create two empty lists
                plant_details = []
                for plant in savedPlants:
                    # Ensure plant.plant_info is not None
                    if plant.plant_info is not None and 'result' in plant.plant_info:
                        # This gets the result portion of the response
                        result = plant.plant_info['result']
                        # Ensure result is not None
                        if result is not None:
                            # Gets the classification portion of the response
                            classification = result['classification']
                            # Ensure classification is not None
                            if classification is not None:
                                # Gets the first suggestion in the response
                                suggestions = classification['suggestions']
                                if suggestions and len(suggestions) > 0:
                                    suggestion = suggestions[0]
                                    # Now safely access suggestion values
                                    # Gets the probabilty of the plant in the images similiarity
                                    plant_prob = suggestion['probability']
                                    # Gets the similiar images in the response 
                                    similar_images = suggestion['similar_images']
                                    # Gets the details portion of the response
                                    details = suggestion['details']
                                    # Gets the common name of the plant
                                    if details['common_names'] is not None:
                                        common_name = details['common_names'][0]
                                        # Gets the name of the plant
                                        plant_name = suggestion['name']
                                    elif details['common_names'] is None and len(suggestions) == 1:
                                        common_name = details['common_name']
                                        plant_name = suggestion['name']
                                    else:
                                        common_name = classification['suggestions'][1]['details']['common_names'][0]
                                        plant_name = classification['suggestions'][1]['name']                                    
                                    # Gets the taxonomy of the plant
                                    taxonomy = details['taxonomy']
                                    list_taxonomy = list(taxonomy.items())[::-1]
                                    reversed_taxonomy = {key: value for key, value in list_taxonomy}
                                    # Gets the description of the plant
                                    if details['description']:
                                        description = details['description']['value']
                                    elif len(result['classification']['suggestions']) == 1 and result['classification']['suggestions'][0]['details']['description'] is None:
                                        description = get_plant_description_wikipedia(common_name)
                                        if description is None:
                                            description = get_plant_description_wikipedia(plant_name)
                                    else: 
                                        description = result['classification']['suggestions'][1]['details']['description']['value']
                                    description = truncate_words(description, 60)
                                    # Gets the synonyms of the plants name
                                    synonyms = details['synonyms']
                                    # Checks if  the plant is edible
                                    edible_parts = details['edible_parts']
                                    # Checks the watering conditions
                                    watering = details['watering']
                                    irrigation_info = watering_message(watering)
                                    identification_results = {
                                        'name': plant_name,
                                        'common_name': common_name,
                                        'taxonomy': reversed_taxonomy,
                                        'description': description,
                                        'edible_part': edible_parts,
                                        'watering': irrigation_info,
                                        'plant_id': plant.id
                                    }
                                    image_base64 = base64.b64encode(plant.image_data).decode('utf-8')
                                    image_url = f"data:image/jpeg;base64,{image_base64}"
                                    plant_details.append({
                                        'image_url': image_url,
                                        'plant_data': identification_results
                                    })  
                theme = session.get('theme', 'light')
                return render_template('history.html', data={'plant_data': plant_details, 'active_page': 'history', 'theme': theme})                       
            # Not logged in
            flash('User has not logged in', 'info')
            return redirect(url_for('signin'))
    except Exception as e:
        print(e)  # For debugging purposes
        if 'username' in session:
            # An error occurred
            return render_template('history.html')
        # Not logged in
        flash('User has not logged in', 'info')
        return redirect(url_for('signin'))

@app.route("/review", methods=['GET'])
def review():
    try:
        reviews = get_reviews()
        theme = session.get('theme', 'light')
        return render_template('review.html', data= {'reviews':reviews, 'theme':theme}) 
    except Exception as e:
        # An error occured
        print(f"An error occurred: {str(e)}")
        flash('An error occured please try again', 'danger')
        return redirect(url_for('setting'))

@app.route("/forgot", methods=['POST', 'GET'])
def forgot():
    try:
        if request.method == 'GET':
            if 'username' in session:
                flash('User account already logged in', 'info')
                return redirect(url_for('home'))
            theme = session.get('theme', 'light')
            return render_template('forgot.html', data={'theme': theme})
        elif request.method == 'POST':
            username = str(request.form['username']).strip()
            name = str(request.form['name']).strip()
            email = str(request.form['email']).strip()
            new_password = str(request.form['password']).strip()
            if len(new_password) < 8:
                flash('Password less than 8', 'danger')
                return redirect(url_for('forgot'))
            if not check_password(new_password):
                flash('Password must contain Letters, Numbers and Symbols', 'danger')
                return redirect('forgot')
            passwordCount = password_count(new_password) 
            if username_exists(username):
                user = get_user(username)
                if username == user.username and name == user.name and email == user.email:
                    if new_password == user.password:
                        flash('Used an old password', 'info')
                        return redirect(url_for('forgot'))
                    if passwordCount != 0:
                        flash('Password has been used', 'warning')
                        return redirect(url_for('forgot'))
                    user.password = new_password
                    db.session.commit()
                    flash('Password updated successfully', 'success')
                    return redirect(url_for('signin'))  
                flash('Details do not match', 'danger')
                return redirect(url_for('forgot'))
            flash('Account not found', 'danger')
            return redirect(url_for('signup'))
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        flash('An error occured please try again', 'danger')
        return redirect(url_for('forgot'))

@app.route("/logout", methods=['GET'])
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('email', None)
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=True)




