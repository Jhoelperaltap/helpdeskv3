from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Configura índices de búsqueda para PostgreSQL'

    def handle(self, *args, **options):
        # Solo ejecutar si estamos usando PostgreSQL
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' not in db_engine:
            self.stdout.write(
                self.style.WARNING('Este comando solo funciona con PostgreSQL. Saltando...')
            )
            return

        with connection.cursor() as cursor:
            try:
                # Crear extensión de búsqueda de texto completo si no existe
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                self.stdout.write(
                    self.style.SUCCESS('Extensión pg_trgm creada/verificada')
                )

                # Crear índices GIN para búsqueda de texto completo
                indexes = [
                    # Índice para títulos de tickets
                    """
                    CREATE INDEX IF NOT EXISTS tickets_ticket_title_gin_idx 
                    ON tickets_ticket USING gin(to_tsvector('spanish', title));
                    """,
                    
                    # Índice para descripciones de tickets
                    """
                    CREATE INDEX IF NOT EXISTS tickets_ticket_description_gin_idx 
                    ON tickets_ticket USING gin(to_tsvector('spanish', description));
                    """,
                    
                    # Índice para referencias de tickets
                    """
                    CREATE INDEX IF NOT EXISTS tickets_ticket_reference_gin_idx 
                    ON tickets_ticket USING gin(reference gin_trgm_ops);
                    """,
                    
                    # Índice para contenido de mensajes
                    """
                    CREATE INDEX IF NOT EXISTS tickets_ticketmessage_content_gin_idx 
                    ON tickets_ticketmessage USING gin(to_tsvector('spanish', content));
                    """,
                    
                    # Índice compuesto para búsquedas complejas
                    """
                    CREATE INDEX IF NOT EXISTS tickets_search_compound_idx 
                    ON tickets_ticket USING gin(
                        (to_tsvector('spanish', title) || 
                         to_tsvector('spanish', description) || 
                         to_tsvector('spanish', reference))
                    );
                    """
                ]

                for index_sql in indexes:
                    cursor.execute(index_sql)
                    self.stdout.write(
                        self.style.SUCCESS(f'Índice creado/verificado')
                    )

                self.stdout.write(
                    self.style.SUCCESS('Todos los índices de búsqueda han sido configurados correctamente')
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al crear índices: {str(e)}')
                )
