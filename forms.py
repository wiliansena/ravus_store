from flask_wtf import FlaskForm
from wtforms import BooleanField, MultipleFileField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional


class ProductForm(FlaskForm):
    class Meta:
        csrf = False

    name = StringField("Nome", validators=[DataRequired()])
    sku = StringField("SKU", validators=[Optional()])
    descricao = TextAreaField("Descricao", validators=[Optional()])
    preco_venda = StringField("Preco de venda", validators=[DataRequired()])
    category_id = SelectField("Categoria", coerce=int, validators=[Optional()], validate_choice=False)
    brand_id = SelectField("Marca", coerce=int, validators=[Optional()], validate_choice=False)
    supplier_id = SelectField("Fornecedor", coerce=int, validators=[Optional()], validate_choice=False)
    color_id = SelectField("Cor", coerce=int, validators=[Optional()], validate_choice=False)
    size_id = SelectField("Tamanho", coerce=int, validators=[Optional()], validate_choice=False)
    min_stock = StringField("Minimo", default="1", validators=[Optional()])
    active = BooleanField("Produto ativo no catalogo", default=True)
    images = MultipleFileField("Imagens")
    submit = SubmitField("Salvar")

    def set_choices(self, categories, brands, suppliers, colors, sizes):
        self.category_id.choices = [(0, "-")] + [(item.id, item.name) for item in categories]
        self.brand_id.choices = [(0, "-")] + [(item.id, item.name) for item in brands]
        self.supplier_id.choices = [(0, "-")] + [(item.id, item.name) for item in suppliers]
        self.color_id.choices = [(0, "-")] + [(item.id, item.name) for item in colors]
        self.size_id.choices = [(0, "-")] + [(item.id, item.name) for item in sizes]
