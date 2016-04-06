SunHead
=======

***This is preview. It's pre-beta, pre-alpha, pre-anything, so don't use it in real projects. 
More work is on the way.***

Framework for building asynchronous websites and micro-services on top of aiohttp

Basic example
-------------

This is how to run your ``epic_app``'s webserver::

    from sunhead.cli.commands.runserver import Runserver
    from sunhead.cli.entrypoint import main as sunhead_main
    
    commands = (
        Runserver("apic_app.server.SubclassOfSunHeadWorkersHttpServer"),   
    )
    
    
    DEFAULT_ENVIRONMENT_VARIABLE = "EPIC_APP_SETTINGS_MODULE"
    GLOBAL_CONFIG_MODULE = "epic_app.settings.base"
    
    
    def main():
        sunhead_main(
            commands=commands,
            settings_ennvar=DEFAULT_ENVIRONMENT_VARIABLE,
            fallback_settings_module=GLOBAL_CONFIG_MODULE
        )
    
    
    if __name__ == '__main__':
        main()

Features
--------

You can run workers from basic console scripts up to the http-servers, connected to messaging streams, queues, etc.
There are REST helper classes, CLI tools, settings incapsulation and other useful things.
