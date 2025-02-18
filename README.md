# RoboGuru


## 📌 Features
- 🚀 Fast and asynchronous API endpoints
- 🔒 JWT-based authentication
- 📄 Database integration with PostgreSQL
- 📡 Firebase authentication support
- 📦 Dependency injection with `Depends`
- 📜 Auto-generated OpenAPI and ReDoc documentation
- 🛠️ Docker support for containerized deployment

## 🏗️ Installation
Ensure you have **Python 3.9+** installed. Then, follow these steps:

```sh
# Clone the repository
git clone https://github.com/your-username/roboguru.git
cd roboguru

# Create and activate virtual environment
python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Environment Variables
Create a `.env` file in the project root and configure it like this:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FIREBASE_PROJECT_ID=your-firebase-project-id
```

## 🚀 Running the Project
After installation, start the FastAPI application using:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Now, open your browser and navigate to:
- 📘 Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📕 ReDoc UI: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🗄️ Database Migration (Using Alembic)
```sh
alembic upgrade head
```

## 🛠️ API Endpoints
### 1️⃣ **User Authentication**
#### 🔹 Firebase Login
```http
POST /firebase-login
```
**Request Body:**
```json
{
  "id_token": "your_firebase_id_token"
}
```
**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "uid": "user-id",
    "email": "user@example.com",
    "access_token": "jwt-token",
    "refresh_token": "refresh-token"
  }
}
```

### 2️⃣ **Protected Route** (JWT Auth Required)
```http
GET /protected-route
Authorization: Bearer your-access-token
```

## 🐳 Docker Support
To run the application using Docker, use the following command:
```sh
docker-compose up --build
```

## 🌍 Deployment
To deploy on **Heroku** or **Railway**, follow these steps:
```sh
git push heroku main
```

## ✨ Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 📜 License
This project is licensed under the MIT License.
