# coding: utf-8

from __future__ import unicode_literals
from django.contrib.admin import site, TabularInline, StackedInline
from django.contrib.admin.options import BaseModelAdmin
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from django.contrib.contenttypes.generic import GenericStackedInline
from reversion import VersionAdmin
from .models import *
from .forms import OeuvreForm, SourceForm, IndividuForm


__all__ = ()


#
# Common
#


class CustomBaseModel(BaseModelAdmin):
    exclude = ('owner',)

    def check_user_ownership(self, request, obj, has_class_permission):
        if not has_class_permission:
            return False
        user = request.user
        if obj is not None and not user.is_superuser and user != obj.owner:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(CustomBaseModel,
                                     self).has_change_permission(request, obj)
        return self.check_user_ownership(request, obj, has_class_permission)

    def has_delete_permission(self, request, obj=None):
        # FIXME: À cause d'un bug dans
        # django.contrib.admin.actions.delete_selected, cette action autorise
        # un utilisateur restreint à supprimer des objets pour lesquels il n'a
        # pas le droit.
        has_class_permission = super(CustomBaseModel,
                                     self).has_delete_permission(request, obj)
        return self.check_user_ownership(request, obj, has_class_permission)

    def queryset(self, request):
        user = request.user
        objects = self.model.objects.all()
        if not user.is_superuser and IS_POPUP_VAR not in request.REQUEST:
            objects = objects.filter(owner=user)
        return objects


#
# Filters
#


class HasRelatedObjectsListFilter(SimpleListFilter):
    title = _('possède des objets liés')
    parameter_name = 'has_related_objects'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Oui')),
            ('0', _('Non')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.with_related_objects()
        if self.value() == '0':
            return queryset.without_related_objects()


def build_boolean_list_filter(class_title, class_parameter_name, filter=None,
                              exclude=None):
    class HasEventsListFilter(SimpleListFilter):
        title = class_title
        parameter_name = class_parameter_name

        def lookups(self, request, model_admin):
            return (
                ('1', _('Oui')),
                ('0', _('Non')),
            )

        def queryset(self, request, queryset):
            if self.value() == '1':
                query = getattr(queryset, 'filter' if filter is not None
                                else 'exclude')
                return query(filter if filter is not None
                             else exclude).distinct()
            if self.value() == '0':
                query = getattr(queryset, 'filter' if exclude is not None
                                else 'exclude')
                return query(exclude if exclude is not None
                             else filter).distinct()

    return HasEventsListFilter


EventHasSourceListFilter = build_boolean_list_filter(_('source'), 'has_source',
                                                     exclude=Q(sources=None))

EventHasProgramListFilter = build_boolean_list_filter(
    _('programme'), 'has_program',
    Q(programme__isnull=False) | Q(relache=True))

SourceHasEventsListFilter = build_boolean_list_filter(
    _('événements'), 'has_events', exclude=Q(evenements=None))

SourceHasProgramListFilter = build_boolean_list_filter(
    _('programme'), 'has_program',
    Q(evenements__programme__isnull=False) | Q(evenements__relache=True))


#
# Inlines
#


class CustomTabularInline(TabularInline, CustomBaseModel):
    extra = 0


class CustomStackedInline(StackedInline, CustomBaseModel):
    extra = 0


class AncrageSpatioTemporelInline(CustomTabularInline):
    model = AncrageSpatioTemporel
    classes = ('grp-collapse grp-closed',)


class OeuvreMereInline(CustomTabularInline):
    model = ParenteDOeuvres
    verbose_name = model._meta.get_field_by_name('mere')[0].verbose_name
    verbose_name_plural = _('œuvres mères')
    fk_name = 'fille'
    raw_id_fields = ('mere',)
    autocomplete_lookup_fields = {
        'fk': ('mere',),
    }
    fields = ('mere', 'type',)
    classes = ('grp-collapse grp-closed',)


class OeuvreFilleInline(CustomTabularInline):
    model = ParenteDOeuvres
    verbose_name = model._meta.get_field_by_name('fille')[0].verbose_name
    verbose_name_plural = _('œuvres filles')
    fk_name = 'mere'
    raw_id_fields = ('fille',)
    autocomplete_lookup_fields = {
        'fk': ('fille',),
    }
    fields = ('type', 'fille')
    classes = ('grp-collapse grp-closed',)


class IndividuParentInline(CustomTabularInline):
    model = ParenteDIndividus
    verbose_name = model._meta.get_field_by_name('parent')[0].verbose_name
    verbose_name_plural = _('individus parents')
    fk_name = 'enfant'
    raw_id_fields = ('parent',)
    autocomplete_lookup_fields = {
        'fk': ('parent',),
    }
    fields = ('parent', 'type',)
    classes = ('grp-collapse grp-closed',)


class IndividuEnfantInline(CustomTabularInline):
    model = ParenteDIndividus
    verbose_name = model._meta.get_field_by_name('enfant')[0].verbose_name
    verbose_name_plural = _('individus enfants')
    fk_name = 'parent'
    raw_id_fields = ('enfant',)
    autocomplete_lookup_fields = {
        'fk': ('enfant',),
    }
    fields = ('type', 'enfant')
    classes = ('grp-collapse grp-closed',)


class OeuvreLieesInline(StackedInline):
    model = Oeuvre
    verbose_name = model._meta.verbose_name
    verbose_name_plural = model._meta.verbose_name_plural
    classes = ('grp-collapse grp-closed',)


class AuteurInline(CustomTabularInline, GenericStackedInline):
    model = Auteur
    verbose_name = model._meta.verbose_name
    verbose_name_plural = model._meta.verbose_name_plural
    raw_id_fields = ('profession', 'individu',)
    autocomplete_lookup_fields = {
        'fk': ['profession', 'individu'],
    }
    classes = ('grp-collapse grp-closed',)


class ElementDeDistributionInline(CustomStackedInline, GenericStackedInline):
    model = ElementDeDistribution
    verbose_name = model._meta.verbose_name
    verbose_name_plural = _('distribution')
    raw_id_fields = ('individus', 'pupitre', 'profession')
    autocomplete_lookup_fields = {
        'fk': ['pupitre', 'profession'],
        'm2m': ['individus'],
    }
    fieldsets = (
        (None, {
            'description': _('Distribution commune à l’ensemble de '
                             'l’événement. Une distribution plus précise peut '
                             'être saisie avec le programme.'),
            'fields': ('individus', 'pupitre', 'profession',),
        }),
    )
    classes = ('grp-collapse grp-open',)


class ElementDeProgrammeInline(CustomStackedInline):
    model = ElementDeProgramme
    verbose_name = model._meta.verbose_name
    verbose_name_plural = _('programme')
    fieldsets = (
        (_('Champs courants'), {
            'fields': (('oeuvre', 'autre',), 'caracteristiques',
                       'distribution', 'numerotation',),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('illustrations', 'documents',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('personnels', 'etat', 'position',),
        }),
    )
    sortable_field_name = 'position'
    raw_id_fields = ('oeuvre', 'caracteristiques', 'distribution',
                     'personnels', 'illustrations', 'documents')
    autocomplete_lookup_fields = {
        'fk': ('oeuvre',),
        'm2m': ('caracteristiques', 'distribution',
                'personnels', 'illustrations', 'documents'),
    }
    classes = ('grp-collapse grp-open',)


#
# ModelAdmins
#


class CustomAdmin(VersionAdmin, CustomBaseModel):
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'owner') is None:
            obj.owner = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if getattr(instance, 'owner') is None:
                instance.owner = request.user
            instance.save()
        formset.save_m2m()


class DocumentAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'document', 'has_related_objects',)
    list_editable = ('nom', 'document',)
    search_fields = ('nom',)


class IllustrationAdmin(CustomAdmin):
    list_display = ('__str__', 'legende', 'image', 'has_related_objects')
    list_editable = ('legende', 'image',)
    search_fields = ('legende',)


class EtatAdmin(CustomAdmin):
    list_display = ('__unicode__', 'nom', 'nom_pluriel', 'public',
                    'has_related_objects')
    list_editable = ('nom', 'nom_pluriel', 'public')


class NatureDeLieuAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel', 'referent',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel', 'referent',)


class LieuAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'parent', 'nature', 'etat', 'link',)
    list_editable = ('nom', 'parent', 'nature', 'etat',)
    search_fields = ('nom', 'parent__nom',)
    list_filter = ('nature', HasRelatedObjectsListFilter)
    raw_id_fields = ('parent', 'illustrations', 'documents',)
    autocomplete_lookup_fields = {
        'fk': ['parent'],
        'm2m': ['illustrations', 'documents'],
    }
    filter_horizontal = ('illustrations', 'documents',)
    readonly_fields = ('__str__', 'html', 'link',)
#    inlines = (AncrageSpatioTemporelInline,)
    fieldsets = (
        (_('Champs courants'), {
            'fields': ('nom', 'parent', 'nature', 'historique',),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('illustrations', 'documents',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('etat', 'notes',),
        }),
#        (_('Champs générés (Méthodes)'), {
#            'classes': ('grp-collapse grp-closed',),
#            'fields': ('__str__', 'html', 'link',),
#        }),
    )


class SaisonAdmin(CustomAdmin):
    list_display = ('__str__', 'lieu', 'debut', 'fin',)
    raw_id_fields = ('lieu',)
    autocomplete_lookup_fields = {
        'fk': ['lieu'],
    }


class ProfessionAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel', 'nom_feminin',
                    'parent', 'classement')
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel', 'nom_feminin', 'parent',
                     'classement')
    raw_id_fields = ('parent', 'illustrations', 'documents')
    autocomplete_lookup_fields = {
        'fk': ('parent',),
        'm2m': ('illustrations', 'documents'),
    }
    fieldsets = (
        (_('Champs courants'), {
            'fields': ('nom', 'nom_pluriel', 'nom_feminin', 'parent',
                       'classement'),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('illustrations', 'documents',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('etat', 'notes',),
        }),
#        (_('Champs générés (Méthodes)'), {
#            'classes': ('grp-collapse grp-closed',),
#            'fields': ('__str__', 'html', 'link',),
#        }),
    )


class AncrageSpatioTemporelAdmin(CustomAdmin):
    list_display = ('__str__', 'calc_date', 'calc_heure', 'calc_lieu',)
    list_filter = (HasRelatedObjectsListFilter,)
    search_fields = ('lieu__nom', 'lieu_approx', 'date_approx',
                     'lieu__parent__nom', 'heure_approx',)
    raw_id_fields = ('lieu',)
    autocomplete_lookup_fields = {
        'fk': ['lieu'],
    }
    fieldsets = (
        (None, {
            'fields': (('date', 'date_approx',), ('heure', 'heure_approx',),
                       ('lieu', 'lieu_approx',))
        }),
    )


class PrenomAdmin(CustomAdmin):
    list_display = ('__str__', 'prenom', 'classement', 'favori',
                    'has_individu')
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('prenom', 'classement', 'favori',)


class TypeDeParenteDIndividusAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel', 'nom_relatif',
                    'nom_relatif_pluriel', 'classement',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel', 'nom_relatif',
                     'nom_relatif_pluriel', 'classement',)


class IndividuAdmin(CustomAdmin):
    list_per_page = 20
    list_display = ('__str__', 'nom', 'calc_prenoms',
                    'pseudonyme', 'titre', 'ancrage_naissance',
                    'ancrage_deces', 'calc_professions', 'etat', 'link',)
    list_editable = ('nom', 'titre', 'etat')
    search_fields = ('nom', 'pseudonyme', 'nom_naissance',
                     'prenoms__prenom',)
    list_filter = ('titre', HasRelatedObjectsListFilter)
    form = IndividuForm
    raw_id_fields = ('prenoms', 'ancrage_naissance', 'ancrage_deces',
                     'professions', 'ancrage_approx',
                     'illustrations', 'documents',)
    related_lookup_fields = {
        'fk': ('ancrage_naissance', 'ancrage_deces', 'ancrage_approx'),
    }
    autocomplete_lookup_fields = {
        'm2m': ('prenoms', 'professions', 'parentes', 'illustrations',
                'documents'),
    }
    readonly_fields = ('__str__', 'html', 'link',)
    inlines = (IndividuParentInline, IndividuEnfantInline)
    fieldsets = (
        (_('Champs courants'), {
            'fields': (('particule_nom', 'nom',), ('prenoms', 'pseudonyme',),
                       ('particule_nom_naissance', 'nom_naissance',),
                       ('titre', 'designation',),
                       ('ancrage_naissance', 'ancrage_deces',),
                       'professions',),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('illustrations', 'documents',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('ancrage_approx', 'biographie', 'etat', 'notes',),
        }),
#        (_('Champs générés (Méthodes)'), {
#            'classes': ('grp-collapse grp-closed',),
#            'fields': ('__str__', 'html', 'link',),
#        }),
    )


class DeviseAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'symbole',)
    list_editable = ('nom', 'symbole',)


class EngagementAdmin(CustomAdmin):
    list_display = ('__str__', 'profession', 'salaire', 'devise',)
    raw_id_fields = ('profession', 'individus',)
    autocomplete_lookup_fields = {
        'fk': ['profession'],
        'm2m': ['individus'],
    }


class TypeDePersonnelAdmin(CustomAdmin):
    list_display = ('nom',)
    list_filter = (HasRelatedObjectsListFilter,)


class PersonnelAdmin(CustomAdmin):
    filter_horizontal = ('engagements',)


class GenreDOeuvreAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel', 'has_related_objects')
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel',)
    search_fields = ('nom', 'nom_pluriel',)
    raw_id_fields = ('parents',)
    autocomplete_lookup_fields = {
        'm2m': ('parents',),
    }


class TypeDeCaracteristiqueDOeuvreAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel', 'classement',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel', 'classement',)


class CaracteristiqueDOeuvreAdmin(CustomAdmin):
    list_display = ('__str__', 'type', 'valeur', 'classement',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('type', 'valeur', 'classement',)
    search_fields = ('type__nom', 'valeur')


class PartieAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'parent', 'classement',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'parent', 'classement',)
    search_fields = ('nom',)
    raw_id_fields = ('professions', 'parent', 'documents', 'illustrations')
    autocomplete_lookup_fields = {
        'm2m': ('professions', 'documents', 'illustrations'),
        'fk': ('parent',),
    }
    fieldsets = (
        (_('Champs courants'), {
            'fields': ('nom', 'nom_pluriel', 'professions', 'parent',
                       'classement'),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('illustrations', 'documents',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('etat', 'notes',),
        }),
#        (_('Champs générés (Méthodes)'), {
#            'classes': ('grp-collapse grp-closed',),
#            'fields': ('__str__', 'html', 'link',),
#        }),
    )


class PupitreAdmin(CustomAdmin):
    list_display = ('__str__', 'partie', 'quantite_min', 'quantite_max',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('partie', 'quantite_min', 'quantite_max',)
    search_fields = ('partie__nom', 'quantite_min', 'quantite_max')
    raw_id_fields = ('partie',)
    autocomplete_lookup_fields = {
        'fk': ['partie'],
    }


class TypeDeParenteDOeuvresAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_relatif', 'nom_relatif_pluriel',
                    'classement',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_relatif', 'nom_relatif_pluriel',
                     'classement',)


class ParenteDOeuvresAdmin(CustomAdmin):
    fields = ('mere', 'type', 'fille',)
    list_display = ('__str__', 'mere', 'type', 'fille',)
    list_editable = ('mere', 'type', 'fille',)
    raw_id_fields = ('fille', 'mere',)
    autocomplete_lookup_fields = {
        'fk': ('fille', 'mere'),
    }


class OeuvreAdmin(CustomAdmin):
    form = OeuvreForm
    list_display = ('__str__', 'titre', 'titre_secondaire', 'genre',
                    'calc_caracteristiques', 'auteurs_html',
                    'ancrage_creation', 'etat', 'link',)
    list_editable = ('genre', 'etat')
    search_fields = ('titre', 'titre_secondaire', 'genre__nom',
                     'auteurs__individu__nom')
    list_filter = ('genre', HasRelatedObjectsListFilter)
    raw_id_fields = ('genre', 'caracteristiques', 'contenu_dans',
                     'ancrage_creation', 'pupitres', 'documents',
                     'illustrations',)
    related_lookup_fields = {
        'fk': ('ancrage_creation',)
    }
    autocomplete_lookup_fields = {
        'fk': ('genre', 'contenu_dans'),
        'm2m': ('caracteristiques', 'pupitres',
                'documents', 'illustrations'),
    }
    readonly_fields = ('__str__', 'html', 'link',)
    inlines = (OeuvreMereInline, OeuvreFilleInline, AuteurInline,)
#    inlines = (ElementDeProgrammeInline,)
    fieldsets = (
        (_('Titre'), {
            'fields': (('prefixe_titre', 'titre',), 'coordination',
                       ('prefixe_titre_secondaire', 'titre_secondaire',),),
        }),
        (_('Autres champs courants'), {
            'fields': ('genre', 'caracteristiques',
                       'ancrage_creation', 'pupitres', 'contenu_dans',),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('documents', 'illustrations',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed', 'wide',),
            'fields': ('lilypond', 'description', 'etat', 'notes',),
        }),
#        (_('Champs générés (Méthodes)'), {
#            'classes': ('grp-collapse grp-closed',),
#            'fields': ('__str__', 'html', 'link',),
#        }),
    )


class ElementDeDistributionAdmin(CustomAdmin):
    list_display = ('__str__', 'pupitre', 'profession',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('pupitre', 'profession',)
    fields = ('individus', 'pupitre', 'profession',)
    raw_id_fields = ('individus', 'pupitre', 'profession',)
    autocomplete_lookup_fields = {
        'fk': ['pupitre', 'profession'],
        'm2m': ['individus'],
    }


class CaracteristiqueDElementDeProgrammeAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel', 'classement',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel', 'classement',)
    search_fields = ('nom', 'nom_pluriel',)


class EvenementAdmin(CustomAdmin):
    list_display = ('__str__', 'relache', 'circonstance',
                    'has_source', 'has_program', 'etat', 'link',)
    list_editable = ('relache', 'circonstance', 'etat')
    search_fields = ('circonstance', 'ancrage_debut__lieu__nom')
    list_filter = ('relache', EventHasSourceListFilter,
                   EventHasProgramListFilter, HasRelatedObjectsListFilter)
    raw_id_fields = ('ancrage_debut', 'ancrage_fin', 'documents',
                     'illustrations',)
    related_lookup_fields = {
        'fk': ('ancrage_debut', 'ancrage_fin'),
    }
    autocomplete_lookup_fields = {
        'm2m': ('documents', 'illustrations'),
    }
    readonly_fields = ('__str__', 'html', 'link')
    inlines = (ElementDeDistributionInline, ElementDeProgrammeInline,)
    fieldsets = (
        (_('Champs courants'), {
            'description': _(
                'Commencez par <strong>saisir ces quelques champs</strong> '
                'avant d’ajouter des <em>éléments de programme</em> '
                'plus bas.'),
            'fields': (('ancrage_debut', 'ancrage_fin',),
                       ('circonstance', 'relache',),),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('documents', 'illustrations',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('etat', 'notes',),
        }),
#        (_('Champs générés (Méthodes)'), {
#            'classes': ('grp-collapse grp-closed',),
#            'fields': ('__str__', 'html', 'link',),
#        }),
    )


class TypeDeSourceAdmin(CustomAdmin):
    list_display = ('__str__', 'nom', 'nom_pluriel',)
    list_filter = (HasRelatedObjectsListFilter,)
    list_editable = ('nom', 'nom_pluriel',)


class SourceAdmin(CustomAdmin):
    form = SourceForm
    list_display = ('nom', 'date', 'type', 'has_events', 'has_program',
                    'owner', 'etat', 'link')
    list_editable = ('type', 'date', 'etat')
    search_fields = ('nom', 'date', 'type__nom', 'numero', 'contenu',
                     'owner__username', 'owner__first_name',
                     'owner__last_name')
    list_filter = ('type', 'nom', SourceHasEventsListFilter,
                   SourceHasProgramListFilter)
    raw_id_fields = ('evenements', 'documents', 'illustrations',)
    related_lookup_fields = {
        'm2m': ['evenements'],
    }
    autocomplete_lookup_fields = {
        'm2m': ['documents', 'illustrations'],
    }
    readonly_fields = ('__str__', 'html',)
    inlines = (AuteurInline,)
    fieldsets = (
        (_('Champs courants'), {
            'fields': ('nom', ('numero', 'page',), ('date', 'type',),
                       'contenu', 'evenements',),
        }),
        (_('Fichiers'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('documents', 'illustrations',),
        }),
        (_('Champs avancés'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('etat', 'notes',),
        }),
        #        (_('Champs générés (Méthodes)'), {
        #            'classes': ('grp-collapse grp-closed',),
        #            'fields': ('__str__', 'html',),
        #        }),
    )

    class Media(object):
        js = [
            '/static/tinymce_setup/tinymce_setup.js',
            '/static/tiny_mce/tiny_mce.js',
        ]


site.register(Document, DocumentAdmin)
site.register(Illustration, IllustrationAdmin)
site.register(Etat, EtatAdmin)
site.register(NatureDeLieu, NatureDeLieuAdmin)
site.register(Lieu, LieuAdmin)
site.register(Saison, SaisonAdmin)
site.register(Profession, ProfessionAdmin)
site.register(AncrageSpatioTemporel, AncrageSpatioTemporelAdmin)
site.register(Prenom, PrenomAdmin)
site.register(TypeDeParenteDIndividus, TypeDeParenteDIndividusAdmin)
site.register(Individu, IndividuAdmin)
site.register(Devise, DeviseAdmin)
site.register(Engagement, EngagementAdmin)
site.register(TypeDePersonnel, TypeDePersonnelAdmin)
site.register(Personnel, PersonnelAdmin)
site.register(GenreDOeuvre, GenreDOeuvreAdmin)
site.register(TypeDeCaracteristiqueDOeuvre, TypeDeCaracteristiqueDOeuvreAdmin)
site.register(CaracteristiqueDOeuvre, CaracteristiqueDOeuvreAdmin)
site.register(Partie, PartieAdmin)
site.register(Pupitre, PupitreAdmin)
site.register(TypeDeParenteDOeuvres, TypeDeParenteDOeuvresAdmin)
site.register(ParenteDOeuvres, ParenteDOeuvresAdmin)
site.register(Oeuvre, OeuvreAdmin)
site.register(ElementDeDistribution, ElementDeDistributionAdmin)
site.register(CaracteristiqueDElementDeProgramme,
              CaracteristiqueDElementDeProgrammeAdmin)
site.register(Evenement, EvenementAdmin)
site.register(TypeDeSource, TypeDeSourceAdmin)
site.register(Source, SourceAdmin)
