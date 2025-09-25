from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.conf import settings
from .models import Ticket

class TicketSearchEngine:
    """
    Motor de búsqueda inteligente para tickets con soporte para PostgreSQL y SQLite
    """
    
    @staticmethod
    def search(queryset, query_text, user=None):
        """
        Realiza búsqueda inteligente en tickets
        
        Args:
            queryset: QuerySet base de tickets
            query_text: Texto a buscar
            user: Usuario que realiza la búsqueda (para filtros de permisos)
        
        Returns:
            QuerySet ordenado por relevancia
        """
        if not query_text or not query_text.strip():
            return queryset
        
        query_text = query_text.strip()
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' in db_engine:
            return TicketSearchEngine._postgresql_search(queryset, query_text)
        else:
            return TicketSearchEngine._sqlite_search(queryset, query_text)
    
    @staticmethod
    def _postgresql_search(queryset, query_text):
        """
        Búsqueda avanzada con PostgreSQL usando full-text search
        """
        # Crear vectores de búsqueda con pesos diferentes
        search_vector = SearchVector(
            'title', weight='A', config='spanish'
        ) + SearchVector(
            'description', weight='B', config='spanish'
        ) + SearchVector(
            'reference', weight='A'
        ) + SearchVector(
            'messages__content', weight='C', config='spanish'
        )
        
        # Crear consulta de búsqueda
        search_query = SearchQuery(query_text, config='spanish')
        
        # Búsqueda por similitud de trigramas para referencias y títulos
        trigram_similarity = TrigramSimilarity('reference', query_text) + \
                           TrigramSimilarity('title', query_text)
        
        return queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query),
            similarity=trigram_similarity
        ).filter(
            Q(search=search_query) | Q(similarity__gt=0.1)
        ).order_by('-rank', '-similarity', '-updated_at').distinct()
    
    @staticmethod
    def _sqlite_search(queryset, query_text):
        """
        Búsqueda básica para SQLite
        """
        # Dividir la consulta en palabras para búsqueda más inteligente
        words = query_text.split()
        
        # Crear filtros para cada palabra
        title_filters = Q()
        desc_filters = Q()
        ref_filters = Q()
        msg_filters = Q()
        
        for word in words:
            title_filters |= Q(title__icontains=word)
            desc_filters |= Q(description__icontains=word)
            ref_filters |= Q(reference__icontains=word)
            msg_filters |= Q(messages__content__icontains=word)
        
        # Combinar todos los filtros
        combined_filter = title_filters | desc_filters | ref_filters | msg_filters
        
        return queryset.filter(combined_filter).distinct().order_by('-updated_at')
    
    @staticmethod
    def get_search_suggestions(query_text, limit=5):
        """
        Obtiene sugerencias de búsqueda basadas en tickets existentes
        """
        if not query_text or len(query_text) < 2:
            return []
        
        # Buscar títulos similares
        suggestions = Ticket.objects.filter(
            title__icontains=query_text
        ).values_list('title', flat=True).distinct()[:limit]
        
        return list(suggestions)
