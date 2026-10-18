import re
from rest_framework import serializers
from modules.identity.serializers import StrictSerializer

class PortfolioInput(StrictSerializer):
    name=serializers.CharField(min_length=3,max_length=100)
    slug=serializers.CharField(max_length=110,required=False)
    description=serializers.CharField(max_length=500,required=False,allow_blank=True)

    def validate_name(self,value):
        if not re.fullmatch(r'\S.{1,98}\S',value):
            raise serializers.ValidationError('Utilisez un nom de 3 à 100 caractères sur une seule ligne.')
        return value

    def validate_slug(self,value):
        value=value.lower()
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',value):
            raise serializers.ValidationError('Utilisez des lettres sans accent, des chiffres et des tirets simples.')
        return value

    def validate(self,attrs):
        if self.partial and not attrs:
            raise serializers.ValidationError({'non_field_errors':['Aucune modification fournie.']})
        return attrs
