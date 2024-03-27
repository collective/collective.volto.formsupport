from collective.volto.formsupport.validation.custom_validators.CharactersValidator import (
    CharactersValidator,
)

maxCharacters = CharactersValidator("maxCharacters", _internal_type="max")
minCharacters = CharactersValidator("minCharacters", _internal_type="min")
custom_validators = [maxCharacters, minCharacters]
