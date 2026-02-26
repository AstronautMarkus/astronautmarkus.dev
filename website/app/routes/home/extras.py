from flask import render_template
from . import home_bp

music_playlists = [
    {
        "iframe": '<iframe width="1897" height="787" src="https://www.youtube.com/embed/jcgDIUvLL6c" title="Di Gi Charat- Party Night" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
    {
        "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/V_D2NSENY0g?si=QcELEtJg9Frvn-CX" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
    {
        "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/6RAehoXcOjI?si=d77dGB8MiuYnksK5" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
    {
        "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/tjlvmb8SGEs?si=eGcllafTKfx5kMif" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
    {
        "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/UsXubuXq1lM?si=nREEgMWazXkGe52j" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
    {
        "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/DwTinTO0o9I?si=3xVEGZZQ9jqoTXkI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
    {
        "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/wbQEA_nxLaE?si=_iljl2KbGGs2NY3R" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    }
]

underground_videos = [
    {
       "iframe": '<iframe width="560" height="315" src="https://www.youtube.com/embed/RQa-7Ql8vZM?si=Qznm0aIHptkJvNbd" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
    },
]

@home_bp.route('/extras')
def extras():
    return render_template('extras.html', playlists=music_playlists, underground_videos=underground_videos)

@home_bp.route('/es/extras')
def extras_es():
    return render_template('/es/extras.html', playlists=music_playlists, underground_videos=underground_videos)