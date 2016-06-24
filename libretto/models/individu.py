# coding: utf-8

from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import connection
from django.db.models import (
    CharField, ForeignKey, ManyToManyField, permalink, PROTECT)
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.html import strip_tags
from django.utils.translation import (
    pgettext_lazy, ungettext_lazy, ugettext, ugettext_lazy as _)
from tinymce.models import HTMLField
from cache_tools import invalidate_object
from common.utils.abbreviate import abbreviate
from common.utils.html import href, sc, hlp
from common.utils.text import str_list, str_list_w_last, ex
from .base import (
    CommonModel, AutoriteModel, UniqueSlugModel, TypeDeParente,
    PublishedManager, PublishedQuerySet, AncrageSpatioTemporel)
from .evenement import Evenement


__all__ = ('TypeDeParenteDIndividus', 'ParenteDIndividus', 'Individu')


class TypeDeParenteDIndividus(TypeDeParente):
    class Meta(object):
        unique_together = ('nom', 'nom_relatif')
        verbose_name = ungettext_lazy('type de parenté d’individus',
                                      'types de parenté d’individus', 1)
        verbose_name_plural = ungettext_lazy(
            'type de parenté d’individus',
            'types de parenté d’individus',
            2)
        ordering = ('classement',)

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        if all_relations:
            return ('parentes',)
        return ()


@python_2_unicode_compatible
class ParenteDIndividus(CommonModel):
    type = ForeignKey('TypeDeParenteDIndividus', related_name='parentes',
                      verbose_name=_('type'), on_delete=PROTECT)
    parent = ForeignKey('Individu', related_name='enfances',
                        verbose_name=_('individu parent'), on_delete=PROTECT)
    enfant = ForeignKey('Individu', related_name='parentes',
                        verbose_name=_('individu enfant'), on_delete=PROTECT)

    class Meta(object):
        verbose_name = ungettext_lazy('parenté d’individus',
                                      'parentés d’individus', 1)
        verbose_name_plural = ungettext_lazy('parenté d’individus',
                                             'parentés d’individus', 2)
        ordering = ('type', 'parent', 'enfant')

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        if all_relations:
            return ('parent', 'enfant')
        return ()

    def clean(self):
        try:
            parent, enfant = self.parent, self.enfant
        except Individu.DoesNotExist:
            return
        if parent and enfant and parent == enfant:
            raise ValidationError(_('Un individu ne peut avoir une '
                                    'parenté avec lui-même.'))

    def __str__(self):
        return ugettext('%(parent)s, %(type)s de %(enfant)s') % {
            'parent': self.parent, 'type': self.type.nom,
            'enfant': self.enfant}


class IndividuQuerySet(PublishedQuerySet):
    def are_feminins(self):
        return all(i.is_feminin() for i in self)


class IndividuManager(PublishedManager):
    def get_queryset(self):
        return IndividuQuerySet(self.model, using=self._db)

    def are_feminins(self):
        return self.get_queryset().are_feminins()


@python_2_unicode_compatible
class Individu(AutoriteModel, UniqueSlugModel):
    particule_nom = CharField(
        _('particule du nom d’usage'), max_length=10, blank=True,
        db_index=True)
    # TODO: rendre le champ nom 'blank'
    nom = CharField(_('nom d’usage'), max_length=200, db_index=True)
    particule_nom_naissance = CharField(
        _('particule du nom de naissance'), max_length=10, blank=True,
        db_index=True)
    nom_naissance = CharField(
        _('nom de naissance'), max_length=200, blank=True, db_index=True,
        help_text=_('Ne remplir que s’il est différent du nom d’usage.'))
    prenoms = CharField(_('prénoms'), max_length=50, blank=True,
                        db_index=True, help_text=ex('Antonio'))
    prenoms_complets = CharField(
        _('prénoms complets'), max_length=100, blank=True, db_index=True,
        help_text=
        ex('Antonio Lucio',
           post=' Ne remplir que s’il existe un ou des prénoms '
                'peu usités pour cet individu.'))
    pseudonyme = CharField(_('pseudonyme'), max_length=200, blank=True,
                           db_index=True)
    DESIGNATIONS = (
        ('S', _('Standard (nom, prénoms et pseudonyme)')),
        ('P', _('Pseudonyme (uniquement)')),
        ('L', _('Nom d’usage (uniquement)')),  # L pour Last name
        ('B', _('Nom de naissance (standard)')),  # B pour Birth name
        ('F', _('Prénom(s) (uniquement)')),  # F pour First name
    )
    designation = CharField(_('affichage'), max_length=1,
                            choices=DESIGNATIONS, default='S')
    TITRES = (
        ('M', _('M.')),
        ('J', _('Mlle')),  # J pour Jouvencelle
        ('F', _('Mme')),
    )
    titre = CharField(pgettext_lazy('individu', 'titre'), max_length=1,
                      choices=TITRES, blank=True, db_index=True)
    naissance = AncrageSpatioTemporel(has_heure=False,
                                      verbose_name=_('naissance'))
    deces = AncrageSpatioTemporel(has_heure=False,
                                  verbose_name=_('décès'))
    professions = ManyToManyField(
        'Profession', related_name='individus', blank=True,
        verbose_name=_('professions'))
    enfants = ManyToManyField(
        'self', through='ParenteDIndividus', related_name='parents',
        symmetrical=False, verbose_name=_('enfants'))
    biographie = HTMLField(_('biographie'), blank=True)

    isni = CharField(
        _('Identifiant ISNI'), max_length=16, blank=True,
        validators=[MinLengthValidator(16),
                    RegexValidator(r'^\d{15}[\dxX]$',
                                   _('Numéro d’ISNI invalide.'))],
        help_text=_('Exemple : « 0000000121269154 » pour Mozart.'))

    objects = IndividuManager()

    class Meta(object):
        verbose_name = ungettext_lazy('individu', 'individus', 1)
        verbose_name_plural = ungettext_lazy('individu', 'individus', 2)
        ordering = ('nom',)
        permissions = (('can_change_status', _('Peut changer l’état')),)

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        relations = ('auteurs', 'elements_de_distribution',)
        if all_relations:
            relations += ('enfants', 'dossiers',)
        return relations

    def get_slug(self):
        invalidate_object(self)
        return self.nom or force_text(self)

    @permalink
    def get_absolute_url(self):
        return 'individu_detail', (self.slug,)

    @permalink
    def permalien(self):
        return 'individu_permanent_detail', (self.pk,)

    def link(self):
        return self.html()
    link.short_description = _('lien')
    link.allow_tags = True

    def oeuvres(self):
        oeuvres = self.auteurs.oeuvres()
        return oeuvres.exclude(extrait_de__in=oeuvres)

    def oeuvres_with_descendants(self):
        return self.auteurs.oeuvres()

    def publications(self):
        return self.auteurs.sources()

    def apparitions(self):
        # FIXME: Gérer la période d’activité des membres d’un groupe.
        sql = """
        SELECT DISTINCT COALESCE(distribution.evenement_id, programme.evenement_id)
        FROM libretto_elementdedistribution AS distribution
        LEFT JOIN libretto_elementdeprogramme AS programme
            ON (programme.id = distribution.element_de_programme_id)
        WHERE distribution.individu_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, (self.pk,))
            evenement_ids = [t[0] for t in cursor.fetchall()]
        return Evenement.objects.filter(id__in=evenement_ids)

    def evenements_referents(self):
        return Evenement.objects.filter(
            programme__oeuvre__auteurs__individu=self).distinct()

    def calc_titre(self, tags=False):
        titre = self.titre
        if not titre:
            return ''

        if tags:
            if titre == 'M':
                return hlp(ugettext('M.'), 'Monsieur')
            elif titre == 'J':
                return hlp(ugettext('M<sup>lle</sup>'), 'Mademoiselle')
            elif titre == 'F':
                return hlp(ugettext('M<sup>me</sup>'), 'Madame')

        if titre == 'M':
            return ugettext('Monsieur')
        elif titre == 'J':
            return ugettext('Mademoiselle')
        elif titre == 'F':
            return ugettext('Madame')

        raise ValueError('Type de titre inconnu, il devrait être M, J, ou F.')

    def is_feminin(self):
        return self.titre in ('J', 'F',)

    def get_particule(self, naissance=False, lon=True):
        particule = (self.particule_nom_naissance if naissance
                     else self.particule_nom)
        if lon and particule and particule[-1] not in "'’":
            return particule + ' '
        return particule

    def calc_professions(self, tags=True):
        if not self.pk:
            return ''
        return str_list_w_last(
            p.html(feminin=self.is_feminin(), tags=tags, caps=i == 0)
            for i, p in enumerate(self.professions.all()))
    calc_professions.short_description = _('professions')
    calc_professions.admin_order_field = 'professions__nom'
    calc_professions.allow_tags = True

    def html(self, tags=True, lon=False,
             show_prenoms=True, designation=None, abbr=True, links=True):
        if designation is None:
            designation = self.designation
        titre = self.calc_titre(tags)
        prenoms = (self.prenoms_complets if lon and self.prenoms_complets
                   else self.prenoms)
        nom = self.nom
        if lon:
            nom = self.get_particule() + nom
        pseudonyme = self.pseudonyme

        def standard(main, prenoms):
            particule = self.get_particule(naissance=(designation == 'B'),
                                           lon=lon)

            l = []
            if nom and not prenoms:
                l.append(titre)
            l.append(main)
            if show_prenoms and (prenoms or particule and not lon):
                if lon:
                    l.insert(max(len(l) - 1, 0), prenoms)
                else:
                    if prenoms:
                        prenoms = abbreviate(prenoms, tags=tags, enabled=abbr)
                    if particule:
                        particule = sc(particule, tags)
                    l.append('(%s)' % ('%s %s' % (prenoms, particule)
                                       if prenoms and particule
                                       else (prenoms or particule)))
            out = str_list(l, ' ')
            if pseudonyme:
                alias = (ugettext('dite') if self.is_feminin()
                         else ugettext('dit'))
                out += ' %s\u00A0%s' % (alias, pseudonyme)
            return out

        if designation in 'SL':
            main = nom
        elif designation == 'F':
            main = prenoms
        elif designation == 'P':
            main = pseudonyme
        elif designation == 'B':
            nom_naissance = self.nom_naissance
            if lon:
                nom_naissance = self.get_particule(True) + nom_naissance
            main = nom_naissance

        main = sc(main, tags)
        out = standard(main, prenoms) if designation in 'SB' else main
        if tags:
            return href(self.get_absolute_url(), out, links)
        return out
    html.short_description = _('rendu HTML')
    html.allow_tags = True

    def nom_seul(self, tags=False, abbr=False, links=False):
        return self.html(tags=tags, lon=False, show_prenoms=False,
                         abbr=abbr, links=links)

    def nom_complet(self, tags=True, designation='S',
                    abbr=False, links=True):
        return self.html(tags=tags, lon=True,
                         designation=designation, abbr=abbr, links=links)

    def related_label(self, tags=False):
        return self.html(tags=tags, abbr=False)
    related_label.short_description = _('individu')

    def related_label_html(self):
        return self.related_label(tags=True)

    def clean(self):
        naissance = self.naissance.date
        deces = self.deces.date
        if naissance and deces and deces < naissance:
            raise ValidationError(_('Le décès ne peut précéder '
                                    'la naissance.'))

    def __str__(self):
        return strip_tags(self.html(tags=False))

    @staticmethod
    def autocomplete_search_fields():
        return (
            'nom__unaccent__icontains',
            'nom_naissance__unaccent__icontains',
            'pseudonyme__unaccent__icontains',
            'prenoms__unaccent__icontains',
        )
