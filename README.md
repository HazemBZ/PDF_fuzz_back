## How this works?
This part is the backend written with Django, and it interacts with a web Frontend written with React that will be linked down bellow

#### Step0
Drop your pdf files inside `assets` folder

#### Step1
Select files that you want to fuzz for keywords. Tap your keyword in the search bar, then click the search button

<p align="center" >
    <img src="images/guide/step1.png" width="600"/>
</p>

#### Step2
Scroll through results, then select an image that interests you

<p align="center" >
    <img src="images/guide/step2.png" width="600"/>
</p>

#### Step4
Look through the pdf page. (more control actions will be provided in the future)

<p align="center" >
    <img src="images/guide/step3.png" width="600"/>
</p>


## Setup
### Manual setup
#### Clone project

```
$ git clone https://github.com/HazemBZ/pdf_fuzz.git
```

#### Install pdfminer

Follow this [link](https://github.com/Belval/pdf2image)

#### Install packages

(activating a virtual environment with tools like `pyenv` or `venv` is highly recommended)

```
$ cd pdf_fuzz
$ pip install -r requirements
```

#### Run server

```
$ python manager.py runserver 8000
```

### With Docker

```
docker build . -t fuzz-backend
docker run -p8000:8000 fuzz-backend
```

## Run web Frontend

Follow this [link](https://github.com/HazemBZ/pdf_fuzz_web.git)
