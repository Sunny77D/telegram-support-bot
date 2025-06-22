localserver:
	python main.py

syncenv: 
	source venv/bin/activate

pipcompile:
	set -x && \
	uv pip compile --annotation-style=line all-requirements.in -o all-requirements.txt --no-strip-extras && \
	uv pip compile -c all-requirements.txt --annotation-style=line requirements.in -o requirements.txt --no-strip-extras && \
	perl -pi -e "s|-c all-requirements.txt, ||g" *.txt && \
	perl -pi -e "s|, -c all-requirements.txt||g" *.txt && \
	uv pip sync requirements.txt
