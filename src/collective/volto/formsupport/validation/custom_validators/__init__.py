from collective.volto.formsupport.validation.custom_validators.CharactersValidator import (
    CharactersValidator,
)
from collective.volto.formsupport.validation.custom_validators.WordsValidator import (
    WordsValidator,
)

maxCharacters = CharactersValidator("maxCharacters", _internal_type="max")
minCharacters = CharactersValidator("minCharacters", _internal_type="min")
maxWords = WordsValidator("maxWords", _internal_type="max")
minWords = WordsValidator("minWords", _internal_type="min")
custom_validators = [maxCharacters, minCharacters, maxWords, minWords]
