from bottle import Bottle, run, request, response
import json
from collections import deque
import gzip
import json
movie_id_to_index = dict()
movies = []
actor_id_to_index = dict()
actors = []

with gzip.open('movies.json.gz', 'rt', encoding='utf8') as f:
    movies = json.load(f)
with gzip.open('actors.json.gz', 'rt', encoding='utf8') as f:
    actors = json.load(f)  
def search_movie(name):
    name_lower = name.lower()
    return [
        {"name": movie[0], "year": movie[2], "index": i}
        for i, movie in enumerate(movies)
        if name_lower in movie[0].lower()
    ]
def get_movie(i):
    movie = movies[i]
    return {
        "name": movie[0],
        "year": movie[2],
        "actors": [{"name": actors[actor_index][0], "index": actor_index} for actor_index in movie[1]]
    }
def search_actor(name):
    name_lower = name.lower()
    return [
        {"name": actor[0], "index": i}
        for i, actor in enumerate(actors)
        if name_lower in actor[0].lower()
    ]
def get_actor(i):
    actor = actors[i]
    return {
        "name": actor[0],
        "movies": [{"name": movies[movie_index][0], "year": movies[movie_index][2], "index": movie_index} for movie_index in actor[1]]
    }

def movie_path(origin, destination):
    if origin == destination:
        return 0, [actors[origin][0]]
    
    # BFS initialization
    queue = deque([(origin, [origin])])
    visited = set([origin])
    
    while queue:
        current_actor, path = queue.popleft()
        
        for movie_index in actors[current_actor][1]:
            for co_actor in movies[movie_index][1]:
                if co_actor == destination:
                    # Found the destination actor
                    full_path = path + [co_actor]
                    path_names = [actors[origin][0]]
                    for i in range(len(full_path) - 1):
                        path_names.append(movies[movies[full_path[i]][1][0]][0])
                        path_names.append(actors[full_path[i + 1]][0])
                    return len(full_path) - 1, path_names
                
                if co_actor not in visited:
                    visited.add(co_actor)
                    queue.append((co_actor, path + [co_actor]))
    
    return -1, []

app = Bottle()

def json_response(data, status=200):
    response.content_type = 'application/json'
    response.status = status
    return json.dumps(data)

@app.route('/movies/<id:int>')
def get_movie_route(id):
    try:
        movie = get_movie(id)
        return json_response(movie)
    except IndexError:
        return json_response({"error": "Movie not found"}, status=404)

@app.route('/movies')
def list_movies():
    try:
        start = int(request.query.start or 0)
        limit = int(request.query.limit or 100)
        order = request.query.order or None
        sorted_movies = sorted(movies, key=lambda x: x[2] if order == 'year' else x[0])
        return json_response(sorted_movies[start:start+limit])
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@app.route('/actors/<id:int>')
def get_actor_route(id):
    try:
        actor = get_actor(id)
        return json_response(actor)
    except IndexError:
        return json_response({"error": "Actor not found"}, status=404)

@app.route('/actors')
def list_actors():
    try:
        start = int(request.query.start or 0)
        limit = int(request.query.limit or 100)
        order = request.query.order or None
        sorted_actors = sorted(actors, key=lambda x: x[0])
        return json_response(sorted_actors[start:start+limit])
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@app.route('/actors/<id:int>/costars')
def get_costars(id):
    try:
        actor = actors[id]
        costars = set()
        for movie_index in actor[1]:
            for co_actor in movies[movie_index][1]:
                if co_actor != id:
                    costars.add(co_actor)
        costar_list = [{"name": actors[co_actor][0], "index": co_actor} for co_actor in costars]
        return json_response(costar_list)
    except IndexError:
        return json_response({"error": "Actor not found"}, status=404)

@app.route('/search/actors/<searchString>')
def search_actors_route(searchString):
    try:
        result = search_actor(searchString)
        return json_response(result)
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@app.route('/search/movies/<searchString>')
def search_movies_route(searchString):
    try:
        filter_params = request.query.filter or None
        filters = {}
        if filter_params:
            for param in filter_params.split(','):
                key, value = param.split(':')
                filters[key] = value
        result = search_movie(searchString)
        if filters:
            result = [movie for movie in result if all(str(movie.get(k)) == v for k, v in filters.items())]
        return json_response(result)
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@app.route('/actors/<id_origin:int>/distance/<id_destination:int>')
def get_distance(id_origin, id_destination):
    try:
        distance, path = movie_path(id_origin, id_destination)
        return json_response({"distance": distance, "path": path})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

if __name__ == '__main__':
    run(app, host='localhost', port=8080)
