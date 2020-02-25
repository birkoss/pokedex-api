from modeltranslation.translator import translator, TranslationOptions

from .models import Pokemon

class PokemonTranslationOptions(TranslationOptions):
	fields = ['name']

translator.register(Pokemon, PokemonTranslationOptions)