from app import create_app

app = create_app('linux')

if __name__ == '__main__':
    app.run()