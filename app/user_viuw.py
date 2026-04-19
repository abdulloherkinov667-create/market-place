from unicodedata import name
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from django.db.models import Q
from .models import UzumProduct, ShopingModel, Users, Order, OrderItem, Like, User_carts
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, TemplateView, DetailView
)

from django.shortcuts import render
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
