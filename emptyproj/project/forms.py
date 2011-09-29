# -*- coding: utf-8 -*-
import logging
import os

from pyramid.i18n import TranslationStringFactory
from formalchemy import fields
from formalchemy import FieldSet, Grid

from project import models
from c2cgeoportail import forms

_ = TranslationStringFactory('project')
log = logging.getLogger(__name__)

# Title
#Title = FieldSet(models.Title)

# UserDetail
#UserDetail = FieldSet(models.UserDetail)
#password = forms.DblPasswordField(UserDetail, UserDetail._password)
#UserDetail.append(password)
#fieldOrder = [UserDetail.username.validate(forms.unique_validator)
#                               .with_metadata(mandatory=''),
#              password, UserDetail.role]
#if hasattr(UserDetail, 'parent_role'):
#    fieldOrder.append(UserDetail.parent_role)
#fieldOrder.extend([UserDetail.title,
#        UserDetail.functionalities.
#                set(renderer=forms.FunctionalityCheckBoxTreeSet)])
#UserDetail.configure(include=fieldOrder)



# TitleGrid
#TitleGrid = Grid(models.Title)

# UserGrid
#UserGrid = Grid(models.UserDetail)
#fieldOrder = [UserDetail.username,
#              UserDetail.title,
#              UserDetail.functionalities,
#              UserDetail.role]
#if hasattr(UserGrid, 'parent_role'):
#    fieldOrder.append(UserDetail.parent_role)
#UserGrid.configure(include=fieldOrder)
