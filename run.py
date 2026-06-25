from app import create_app

app = create_app()


if __name__ == "__main__":
    # Permite conexoes externas na rede local, igual ao padrao usado no saasforce.
    app.run(host="0.0.0.0", port=5000)
