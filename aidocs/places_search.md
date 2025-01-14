Once you have a place ID, you can request more details about a particular establishment or point of interest by initiating a Place Details (New) request. A Place Details (New) request returns more comprehensive information about the indicated place such as its complete address, phone number, user rating and reviews.

There are many ways to obtain a place ID. You can use:

Text Search (New) or Nearby Search (New)
Geocoding API
Routes API
Address Validation API
Place Autocomplete
The API Explorer lets you make live requests so that you can get familiar with the API and the API options:

Try it!
Place Details (New) requests
A Place Details request is an HTTP GET request in the form:


https://places.googleapis.com/v1/places/PLACE_ID
Pass all parameters as URL parameters or in headers as part of the GET request. For example:


https://places.googleapis.com/v1/places/ChIJj61dQgK6j4AR4GeTYWZsKWw?fields=id,displayName&key=API_KEY
Or in a cURL command:


curl -X GET -H 'Content-Type: application/json' \
-H "X-Goog-Api-Key: API_KEY" \
-H "X-Goog-FieldMask: id,displayName" \
https://places.googleapis.com/v1/places/ChIJj61dQgK6j4AR4GeTYWZsKWw
Place Details (New) responses
Place Details (New) returns a JSON object as a response. In the response:

The response is represented by a Place object. The Place object contains detailed information about the place.
The FieldMask passed in the request specifies the list of fields returned in the Place object.
The complete JSON object is in the form:


{
  "name": "places/ChIJkR8FdQNB0VQRm64T_lv1g1g",
  "id": "ChIJkR8FdQNB0VQRm64T_lv1g1g",
  "displayName": {
    "text": "Trinidad"
  }
  ...
}
Required parameters
FieldMask
Specify the list of fields to return in the response by creating a response field mask. Pass the response field mask to the method by using the URL parameter $fields or fields, or by using the HTTP header X-Goog-FieldMask. There is no default list of returned fields in the response. If you omit the field mask, the method returns an error.

Field masking is a good design practice to ensure that you don't request unnecessary data, which helps to avoid unnecessary processing time and billing charges.

Specify a comma-separated list of place data types to return. For example, to retrieve the display name and the address of the place.


X-Goog-FieldMask: displayName,formattedAddress
Note: Spaces are not allowed anywhere in the field list.
Use * to retrieve all fields.


X-Goog-FieldMask: *
Wildcard "*" selects all fields. However, while that wildcard is fine to use in development, Google discourage the use of the wildcard (*) response field mask in production because of the large amount of data that can be returned.
Further guidance for using iconMaskBaseUri and iconBackgroundColor can be found in Place Icons section.
Specify one or more of the following fields:

The following fields trigger the Place Details (IDs Only) SKU:

attributions, id, name*, photos

* The name field contains the place resource name in the form: places/PLACE_ID. Use displayName to access the text name of the place.

The following fields trigger the Place Details (Location Only) SKU:

addressComponents, adrFormatAddress, formattedAddress, location, plusCode, shortFormattedAddress, types, viewport

The following fields trigger the Place Details (Basic) SKU:

accessibilityOptions, businessStatus, containingPlaces, displayName, googleMapsLinks*, googleMapsUri, iconBackgroundColor, iconMaskBaseUri, primaryType, primaryTypeDisplayName, pureServiceAreaBusiness, subDestinations, utcOffsetMinutes

* The googleMapsLinks field is in the pre-GA Preview stage and there is no charge, meaning billing is $0, for usage during Preview.

The following fields trigger the Place Details (Advanced) SKU:

currentOpeningHours, currentSecondaryOpeningHours, internationalPhoneNumber, nationalPhoneNumber, priceLevel, priceRange, rating, regularOpeningHours, regularSecondaryOpeningHours, userRatingCount, websiteUri

The following fields trigger the Place Details (Preferred) SKU:

allowsDogs, curbsidePickup, delivery, dineIn, editorialSummary, evChargeOptions, fuelOptions, goodForChildren, goodForGroups, goodForWatchingSports, liveMusic, menuForChildren, parkingOptions, paymentOptions, outdoorSeating, reservable, restroom, reviews, routingSummaries,* servesBeer, servesBreakfast, servesBrunch, servesCocktails, servesCoffee, servesDessert, servesDinner, servesLunch, servesVegetarianFood, servesWine, takeout

* Text Search and Nearby Search only

placeId
A textual identifier that uniquely identifies a place, returned from a Text Search (New) or Nearby Search (New). For more information about place IDs, see the place ID overview.

The string places/PLACE_ID is also called the place resource name. In the response from a Place Details (New), Nearby Search (New), and Text Search (New) request, this string is contained in the name field of the response. The standalone place ID is contained in the id field of the response.

Note: In the existing Place Details, the name field of the response contained the human-readable name for the place. In the new API, that field is now called displayName.
Optional parameters
languageCode
The language in which to return results.

See the list of supported languages. Google often updates the supported languages, so this list may not be exhaustive.
If languageCode is not supplied, the API defaults to en. If you specify an invalid language code, the API returns an INVALID_ARGUMENT error.
The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component.
If a name is not available in the preferred language, the API uses the closest match.
The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another.
regionCode
The region code used to format the response, specified as a two-character CLDR code value. There is no default value.

If the country name of the formattedAddress field in the response matches the regionCode, the country code is omitted from formattedAddress. This parameter has no effect on adrFormatAddress, which always includes the country name, or on shortFormattedAddress, which never includes it.

Most CLDR codes are identical to ISO 3166-1 codes, with some notable exceptions. For example, the United Kingdom's ccTLD is "uk" (.co.uk) while its ISO 3166-1 code is "gb" (technically for the entity of "The United Kingdom of Great Britain and Northern Ireland"). The parameter can affect results based on applicable law.

sessionToken
Session tokens are user-generated strings that track Autocomplete (New) calls as "sessions." Autocomplete (New) uses session tokens to group the query and place selection phases of a user autocomplete search into a discrete session for billing purposes. Session tokens are passed into Place Details (New) calls that follow Autocomplete (New) calls. For more information, see Session tokens.

Place Details example
The following example requests the details of a place by placeId:


curl -X GET -H 'Content-Type: application/json' \
-H "X-Goog-Api-Key: API_KEY" \
-H "X-Goog-FieldMask: id,displayName" \
https://places.googleapis.com/v1/places/ChIJj61dQgK6j4AR4GeTYWZsKWw
Note that the X-Goog-FieldMask header specifies that the response contains the following data fields: id,displayName. The response is then in the form:


{
  "id": "ChIJj61dQgK6j4AR4GeTYWZsKWw",
  "displayName": {
    "text": "Googleplex",
    "languageCode": "en"
  }
}
Add more data types to the field mask to return additional information. For example, add formattedAddress,plusCode to include the address and Plus Code in the response:


curl -X GET -H 'Content-Type: application/json' \
-H "X-Goog-Api-Key: API_KEY" \
-H "X-Goog-FieldMask: id,displayName,formattedAddress,plusCode" \
https://places.googleapis.com/v1/places/ChIJj61dQgK6j4AR4GeTYWZsKWw
The response is now in the form:


{
  "id": "ChIJj61dQgK6j4AR4GeTYWZsKWw",
  "formattedAddress": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
  "plusCode": {
    "globalCode": "849VCWC7+RW",
    "compoundCode": "CWC7+RW Mountain View, CA, USA"
  },
  "displayName": {
    "text": "Googleplex",
    "languageCode": "en"
  }
}

Nearby Search
Basic

1,000
Requests
$32
Advanced

1,000
Requests
$35
Preferred

1,000
Requests
$40
Place Details
Basic

1,000
Requests
$17
Advanced

1,000
Requests
$20
Preferred

1,000
Requests