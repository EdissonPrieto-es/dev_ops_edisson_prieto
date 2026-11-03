def test_pipeline_fallido_intencional():
    """Parte 7: prueba que falla a proposito para demostrar que el pipeline se detiene.

    CodeBuild falla en la fase pre_build, no se genera el artefacto y no hay despliegue.
    Se elimina (o se corrige) en el commit que restaura el pipeline exitoso.
    """
    assert 1 + 1 == 3, "Fallo intencional para la Parte 7 (pipeline fallido)"
