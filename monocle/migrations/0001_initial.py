# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ThirdPartyProvider'
        db.create_table('monocle_thirdpartyprovider', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('api_endpoint', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('expose', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('monocle', ['ThirdPartyProvider'])

        # Adding model 'URLScheme'
        db.create_table('monocle_urlscheme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scheme', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('provider', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_schemes', to=orm['monocle.ThirdPartyProvider'])),
        ))
        db.send_create_signal('monocle', ['URLScheme'])


    def backwards(self, orm):
        # Deleting model 'ThirdPartyProvider'
        db.delete_table('monocle_thirdpartyprovider')

        # Deleting model 'URLScheme'
        db.delete_table('monocle_urlscheme')


    models = {
        'monocle.thirdpartyprovider': {
            'Meta': {'ordering': "('api_endpoint', 'resource_type')", 'object_name': 'ThirdPartyProvider'},
            'api_endpoint': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'expose': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'monocle.urlscheme': {
            'Meta': {'object_name': 'URLScheme'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_schemes'", 'to': "orm['monocle.ThirdPartyProvider']"}),
            'scheme': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['monocle']