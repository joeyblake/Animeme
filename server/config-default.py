class Config(object):
    DEBUG = False
    TESTING = False
    S3_KEY = AWSS3KEY
    S3_SECRET = AWSS3SECRET
    S3_BUCKET = "animeme"
    S3_UPLOAD_DIRECTORY = "/vagrant/gifs/"
    SCRATCH_DIR = "/vagrant/scratch/"

class ProductionConfig(Config):
    S3_UPLOAD_DIRECTORY = "/var/www/animeme/gifs/"
    SCRATCH_DIR = "/var/www/animeme/scratch/"

class DevelopmentConfig(Config):
    DEBUG = True
    S3_UPLOAD_DIRECTORY = "/vagrant/gifs/"
    SCRATCH_DIR = "/vagrant/scratch/"

class TestingConfig(Config):
    TESTING = True