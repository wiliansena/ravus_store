from app import create_app
from models import ProductImage
from utils_uploads import gerar_thumbnail_produto


app = create_app()

with app.app_context():
    total = 0
    for image in ProductImage.query.order_by(ProductImage.id).all():
        if gerar_thumbnail_produto(image.filename):
            total += 1
    print(f"Miniaturas geradas: {total}")
