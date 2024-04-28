from flask import Flask, render_template, request, session, redirect, url_for
from flask.cli import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visitors.db'  # Configure the database URI
app.secret_key = os.getenv('SECRET_KEY')  # Set a secret key for session handling
db = SQLAlchemy(app)

# Configure the upload directory
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Define the Visitor model
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), unique=True, nullable=False)
    visit_count = db.Column(db.Integer, default=1)


# Define the ImageCount model
class ImageCount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)


# Create the database tables
with app.app_context():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if 'authenticated' not in session:
        # Prompt for password
        password = request.form.get('password')
        if password == os.getenv('SECRET_PASSWORD'):
            session['authenticated'] = True
            return redirect(url_for('upload_file'))
        else:
            return render_template('login.html')
    if request.method == 'POST':
        # Check if the file is present in the request
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return 'No selected file'

        # Process the image using your existing Python script
        result = process_image(file, 30, 14)

        # Increment the image count
        image_count = ImageCount.query.first()
        if image_count:
            image_count.count += 1
        else:
            image_count = ImageCount(count=1)
            db.session.add(image_count)

        db.session.commit()

        return render_template('result.html', result=result)

    # Get the visitor's IP address
    visitor_ip = request.remote_addr

    # Check if the visitor already exists in the database
    visitor = Visitor.query.filter_by(ip_address=visitor_ip).first()
    if visitor:
        # If the visitor exists, increment the visit count
        visitor.visit_count += 1
    else:
        # If the visitor is new, create a new Visitor record
        new_visitor = Visitor(ip_address=visitor_ip)
        db.session.add(new_visitor)

    db.session.commit()

    # Get the total number of unique visitors
    total_visitors = Visitor.query.count()

    # Get the total number of generated images
    image_count = ImageCount.query.first()
    total_images = image_count.count if image_count else 0

    return render_template('upload.html', total_visitors=total_visitors, total_images=total_images)


def process_image(file, output_width, output_height):
    img = Image.open(file)
    ret = '======PLACEHOLDER NAME======\\n'

    resized_img = img.resize((output_width, output_height), Image.Resampling.LANCZOS)

    for y in range(output_height):
        row = []
        for x in range(output_width):
            pixel = resized_img.getpixel((x, y))

            # Check if the pixel has an alpha channel
            if len(pixel) == 4 and pixel[3] == 0:
                hex_value = '#0D0E0E'
            else:
                r, g, b = pixel[:3]
                hex_value = '#{:02x}{:02x}{:02x}'.format(r, g, b)

            # file.write(f'<color:{hex_value}>█</color>')
            ret += f'<color:{hex_value}>█</color>'

        ret += '\\n'
        # file.write('\\n')

    return ret


if __name__ == '__main__':
    app.run()
