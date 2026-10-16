from django.db import migrations, models


class Migration(migrations.Migration):
    """O código da peça passa a ser gerado automaticamente (PEC-00001).

    O código digitado antes é preservado como "código do fabricante" (referencia).
    """

    dependencies = [
        ('oficina', '0003_fornecedor_peca_movimentacaoestoque_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='peca',
            old_name='codigo',
            new_name='referencia',
        ),
        migrations.AlterField(
            model_name='peca',
            name='referencia',
            field=models.CharField(
                blank=True, max_length=40, verbose_name='código do fabricante',
                help_text='Opcional. Código/part number da peça no catálogo do fabricante.',
            ),
        ),
    ]
