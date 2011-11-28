from c2cgeoportal.models import DBSession, Layer
import transaction

def upgrade(migrate_engine):
    layers = DBSession.query(Layer).all()
    for layer in layers:
        layer.isVisible = True
    transaction.commit()

def downgrade(migrate_engine):
    pass
