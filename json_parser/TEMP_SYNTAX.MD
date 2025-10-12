### Components are separated by two consecutive new-lines

### Abstract 
- Removed and saved from Mistral OCR. 
- Not to be summarised but still saved. 

### Headings 
- Everything that starts with a hashtag, one or more with a space in between. 
- Number of hashtags 1 to 6 

### Paragraph 
- Any string of texts without a preceding hashtag or space. 
- Can contain 1 new-line in between string of texts 

##### In-Line Citation 
- Replaced with [] through API call.
- Multiple citations separated by comma. 
- Sub-element of Paragraph

### Tables 
- If caption exists, it will be placed below the table, after one new-line. 
- Tables will be a bunch of [\\\||||] with data in between, cleaned with API call as well. 

### Figure & Images 
- Images will just be references as they will be pre-saved. 
- Paragraphs will exist one new-line after the image's location. 

### Latex Formula 
- Mistral Output OCR 
- Remains unchanged from output. 
- Latex references need to be saved and be part of the formula. 
- Optional key / references to the Latex formula. Saved as two part,
	- Latex Formula + Optional Key or Reference. 

#### References / Citations 
- Convert all references to **IEEE** Citation format
- Post-Mistral OCR output 

#### Author Section 
- Cleaned and parsed prior to Mistral OCR
- Optional Title if available Name, Institution, Contact, Website, (subject to availability)
- Separated by one new-line for each credential / author
- Each field separated by semi-colon (Anam Milfer ; University of Melbourne ; )

#### Table of Contents 
- Removed prior to Mistral OCR. 
- Saved to keep as additional feature, markdown. 

#### Code 
- Mistral OCR ``` test ``` , code kept in this format. 
- Code blocks cleaned up after Mistral OCR output. 

#### Bullet Points / Numbered Lists 
- A new-line in between the top and bottom of any set of bullet points or numbered lists.

#### Overlay or blocks of text / information 
- Noted as (>>) in the front