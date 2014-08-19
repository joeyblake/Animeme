import os, config, urllib2
os.environ['SDL_VIDEODRIVER'] = 'dummy'
from uuid import uuid4
import subprocess, hashlib, boto, os.path
from subprocess import call
from moviepy.editor import *
from flask import Flask, request, url_for
from flask.ext.jsonpify import jsonify
from werkzeug import secure_filename

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

@app.route("/", methods=['GET', 'POST'])
def process():
  url = urllib2.unquote(request.args.get('url'))
  start = urllib2.unquote(request.args.get('start'))
  start = (int(start.split(',')[0]),float(start.split(',')[-1]))
  stop = urllib2.unquote(request.args.get('stop'))
  stop = (int(stop.split(',')[0]),float(stop.split(',')[-1]))
  
  try:
    t_text = request.args.get('t_text')
  except (TypeError, ValueError):
    t_text = None
      
  try:
    b_text = request.args.get('b_text')
  except (TypeError, ValueError):
    b_text = None   
  
  try:
    t_pos = int(request.args.get('t_pos'))
  except (ValueError, TypeError):
    t_pos = 0
  
  try:
    b_pos = int(request.args.get('b_pos'))
  except (ValueError, TypeError):
    b_pos = 270

  url = download_video(url)
  return gifify(url, start, stop, t_text, t_pos, b_text, b_pos)

def download_video(url):
  cmd = ["youtube-dl", "--get-filename", "-o", "%(title)s.%(ext)s", url, "--restrict-filenames"]
  vid_name = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].strip()
  downloaded = subprocess.Popen(["youtube-dl", "-o", app.config['SCRATCH_DIR']+vid_name, url, '--restrict-filenames']).communicate()
  return app.config['SCRATCH_DIR']+vid_name

def gifify(url, start, stop, t_text=None, t_pos=0, b_text=None, b_pos=280):
  output_filename = md5(url)+'.gif'
  comp = []
  vid = VideoFileClip(url, audio=False).\
              subclip(start,stop).\
              resize(height=330).\
              on_color((640,330),(0, 0, 0),("center", "top")).\
              speedx(0.5).\
              fx( time_symetrize )
  comp.append(vid)
  # Many options are available for the text (requires ImageMagick)
  if ( t_text ) :
    t_text = TextClip(t_text,
                    align="center",
                    method="caption",
                    size=(640, None),
                    fontsize=30, color='white',
                    stroke_color='#333333', stroke_width=0.5,
                    font=app.config["LIB_DIR"]+'fonts/Coda-Caption-Heavy.ttf', interline=0).\
                set_pos((0,t_pos)).\
                set_duration(vid.duration)
    comp.append(t_text)

  if ( b_text ) :
    b_text = TextClip(b_text,
                    align="center",
                    method="caption",
                    size=(640, None),
                    fontsize=30, color='white',
                    stroke_color='#333333', stroke_width=0.5,
                    font=app.config["LIB_DIR"]+'fonts/Coda-Caption-Heavy.ttf', interline=0).\
                set_pos((0,b_pos)).\
                set_duration(vid.duration)
    comp.append(b_text)

  CompositeVideoClip( comp ).\
      to_gif(app.config['S3_UPLOAD_DIRECTORY']+output_filename, fps=10, fuzz=2)
  return s3_upload(output_filename)

def s3_upload(source_filename,acl='public-read'):
    source_filename = app.config['S3_UPLOAD_DIRECTORY']+source_filename
    source_extension = os.path.splitext(source_filename)[1]

    destination_filename = uuid4().hex + source_extension

    # Connect to S3
    conn = boto.connect_s3(app.config["S3_KEY"], app.config["S3_SECRET"])
    b = conn.get_bucket(app.config["S3_BUCKET"])

    # Upload the File
    sml = b.new_key("/".join([app.config["S3_UPLOAD_DIRECTORY"],destination_filename]))
    sml.set_contents_from_filename(source_filename)

    # Set the file's permissions.
    sml.set_acl(acl)

    return jsonify(s3file=sml.generate_url(0, query_auth=False, force_http=True))

def md5(string):
  return hashlib.md5(string).hexdigest()

if __name__ == "__main__":
    app.run(host='0.0.0.0')